import streamlit as st
import gspread
import json
from PIL import Image, UnidentifiedImageError, ImageOps
from datetime import datetime
from google.oauth2.credentials import Credentials
import io
import uuid
import pytz
import time
import cloudinary
import cloudinary.uploader

st.set_page_config(page_title="出品画面", layout="centered")
st.title("出品画面")

# ============================================
# ✅ uploader_key を初期化（画像アップロードの安定化）
# ============================================
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = str(uuid.uuid4())

# ============================================
# 🔐 ログインチェック
# ============================================
if st.session_state.get("logged_in"):
    with st.container(horizontal=True):
        st.markdown(f"👤 ログイン中：**{st.session_state['username']}** さん")
        if st.button("ログアウト"):
            st.session_state.clear()
            st.rerun()
else:
    st.warning("ログインしてください")
    if st.button("ログイン画面へ"):
        st.switch_page("app.py")
    st.stop()

# ============================================
# ✨ 編集モード判定
# ============================================
edit_mode = "edit_product" in st.session_state
edit_item = st.session_state.get("edit_product") if edit_mode else None

# ============================================
# 🔑 OAuth認証
# ============================================
try:
    creds_dict = json.loads(st.secrets["OAUTH_TOKEN"])
    creds = Credentials.from_authorized_user_info(creds_dict)
    gc = gspread.authorize(creds)
    sheet = gc.open(st.secrets["PRODUCT_SHEET_NAME"]).sheet1
except Exception as e:
    st.error(f"Google Sheetsの認証に失敗しました: {e}")
    st.stop()

# ============================================
# ☁ Cloudinary認証
# ============================================
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)

# ============================================
# 📝 初期化（session_state）
# ============================================
if "form_initialized" not in st.session_state:
    st.session_state["name"] = edit_item["商品名"] if edit_mode else ""
    st.session_state["price"] = int(edit_item["価格"]) if edit_mode else 0
    st.session_state["category"] = edit_item["カテゴリ"] if edit_mode else "衣類"
    st.session_state["condition"] = edit_item["状態"] if edit_mode else "新品"
    st.session_state["desc"] = edit_item["説明"] if edit_mode else ""
    st.session_state["form_initialized"] = True

# ============================================
# 📝 入力フォーム（session_stateベース）
# ============================================

st.warning("出品時のみ、私用端末（スマホ等）で登録してください。※会社端末は画像アップロード不可のため")

st.image("QRdigicari.png", width=100)

st.session_state["name"] = st.text_input("商品名", st.session_state["name"])
st.session_state["price"] = st.number_input("価格", min_value=0, value=st.session_state["price"])

category_list = ["衣類", "雑貨", "日用品", "本", "スポーツ", "その他"]
st.session_state["category"] = st.selectbox(
    "カテゴリ",
    category_list,
    index=category_list.index(st.session_state["category"])
)

condition_list = ["新品", "中古"]
st.session_state["condition"] = st.selectbox(
    "状態",
    condition_list,
    index=condition_list.index(st.session_state["condition"])
)

st.session_state["desc"] = st.text_area("説明", st.session_state["desc"])

# ============================================
# 🖼 既存画像プレビュー（編集モードのみ）
# ============================================
if edit_mode:
    st.markdown("### 現在の画像")
    st.image(edit_item["画像URL"], width=200)
    if edit_item.get("画像URLサブ1"):
        st.image(edit_item["画像URLサブ1"], width=200)
    if edit_item.get("画像URLサブ2"):
        st.image(edit_item["画像URLサブ2"], width=200)

# ============================================
# 🖼 新しい画像アップロード（文言変更済）
# ============================================
st.markdown("### 画像アップロード（メイン画像（1枚目）：必須、サブ画像（2・3枚目）：任意）")

st.session_state["image_main"] = st.file_uploader(
    "メイン画像",
    type=["jpg", "jpeg", "png"],
    key=f"main_{st.session_state['uploader_key']}"
)

st.session_state["image_sub1"] = st.file_uploader(
    "サブ画像1",
    type=["jpg", "jpeg", "png"],
    key=f"sub1_{st.session_state['uploader_key']}"
)

st.session_state["image_sub2"] = st.file_uploader(
    "サブ画像2",
    type=["jpg", "jpeg", "png"],
    key=f"sub2_{st.session_state['uploader_key']}"
)

submit = st.button("保存する" if edit_mode else "出品する")

# ============================================
# ☁ 画像アップロード関数
# ============================================
def process_and_upload(file):
    try:
        img = Image.open(file)
        img = ImageOps.exif_transpose(img)
    except UnidentifiedImageError:
        return None

    max_width = 512
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    result = cloudinary.uploader.upload(buf, folder="products")
    return result["secure_url"]

# ============================================
# 🚀 保存処理（編集モード or 新規出品）
# ============================================
if submit:

    if not st.session_state["name"] or not st.session_state["price"] or not st.session_state["desc"]:
        st.warning("商品名・価格・説明は必須です。")
        st.stop()

    # ----------------------------------------
    # ✨ 編集モード
    # ----------------------------------------
    if edit_mode:

        main_url = edit_item["画像URL"]
        sub1_url = edit_item.get("画像URLサブ1", "")
        sub2_url = edit_item.get("画像URLサブ2", "")

        if st.session_state["image_main"]:
            main_url = process_and_upload(st.session_state["image_main"])
        if st.session_state["image_sub1"]:
            sub1_url = process_and_upload(st.session_state["image_sub1"])
        if st.session_state["image_sub2"]:
            sub2_url = process_and_upload(st.session_state["image_sub2"])

        all_data = sheet.get_all_records()
        row_index = next((i for i, row in enumerate(all_data)
                          if row.get("商品ID") == edit_item["商品ID"]), None)

        if row_index is None:
            st.error("商品が見つかりませんでした。")
            st.stop()

        row_num = row_index + 2

        update_row = [
            edit_item["商品ID"], st.session_state["name"], st.session_state["price"],
            st.session_state["desc"], st.session_state["condition"],
            main_url, sub1_url, sub2_url,
            edit_item["出品者"], edit_item["出品者名"],
            edit_item["投稿日時"], st.session_state["category"],
            edit_item.get("購入者", ""), edit_item.get("購入者名", ""),
            edit_item.get("購入日時", ""), edit_item["ステータス"]
        ]

        sheet.update(f"A{row_num}:P{row_num}", [update_row])

        st.success("商品情報を更新しました！")
        st.session_state.pop("edit_product")
        st.switch_page("pages/7_マイページ（出品）.py")
        st.stop()

    # ----------------------------------------
    # ✨ 新規出品
    # ----------------------------------------
    else:
        if not st.session_state["image_main"]:
            st.warning("メイン画像は必須です。")
            st.stop()

        main_url = process_and_upload(st.session_state["image_main"])
        sub1_url = process_and_upload(st.session_state["image_sub1"]) if st.session_state["image_sub1"] else ""
        sub2_url = process_and_upload(st.session_state["image_sub2"]) if st.session_state["image_sub2"] else ""

        product_id = str(uuid.uuid4())
        jst = pytz.timezone("Asia/Tokyo")
        now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

        new_row = [
            product_id, st.session_state["name"], st.session_state["price"],
            st.session_state["desc"], st.session_state["condition"],
            main_url, sub1_url, sub2_url,
            st.session_state["id"], st.session_state["username"],
            now, st.session_state["category"],
            "", "", "", "出品中"
        ]

        sheet.append_row(new_row)

        # 完了メッセージを session_state に保存
        st.session_state["post_message"] = f"{st.session_state['username']} さん、商品を出品しました。ありがとうございます。"

        # 入力値を初期化
        for key in ["name", "price", "category", "condition", "desc", "form_initialized"]:
            if key in st.session_state:
                st.session_state.pop(key)

        # file_uploader の key をリセット（画像クリアの決定版）
        st.session_state["uploader_key"] = str(uuid.uuid4())

        st.rerun()

# ============================================
# 🎉 完了メッセージ（rerun後も表示）
# ============================================
if "post_message" in st.session_state:
    st.success(st.session_state["post_message"])
    st.session_state.pop("post_message")

# ============================================
# 📌 フッターメニュー
# ============================================
st.divider()
st.markdown("### 📌 メニュー")
with st.container(horizontal=True):
    st.page_link("pages/2_商品検索.py", label="商品検索")
    st.page_link("pages/3_出品画面.py", label="出品画面")
    st.page_link("pages/7_マイページ（出品）.py", label="マイページ（出品）")
    st.page_link("pages/6_マイページ（購入）.py", label="マイページ（購入）")