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
# 🔐 ログインチェック
# ============================================
if st.session_state.get("logged_in"):
    with st.container(horizontal=True):
        st.markdown(f"👤 ログイン中：**{st.session_state['username']}** さん")
        if st.button("ログアウト"):
            st.session_state["logged_in"] = False
            st.session_state.pop("id", None)
            st.session_state.pop("username", None)
            st.rerun()
else:
    st.warning("ログインしてください")
    if st.button("ログイン画面へ"):
        st.switch_page("app.py")
        st.stop()
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
# 📝 入力フォーム（編集モード対応）
# ============================================
name = st.text_input("商品名", value=edit_item["商品名"] if edit_mode else "")
price = st.number_input("価格", min_value=0, value=int(edit_item["価格"]) if edit_mode else 0)

category_list = ["衣類", "雑貨", "日用品", "本", "スポーツ", "その他"]
category = st.selectbox(
    "カテゴリ",
    category_list,
    index=category_list.index(edit_item["カテゴリ"]) if edit_mode else 0
)

condition_list = ["新品", "中古"]
condition = st.selectbox(
    "状態",
    condition_list,
    index=condition_list.index(edit_item["状態"]) if edit_mode else 0
)

desc = st.text_area("説明", value=edit_item["説明"] if edit_mode else "")

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

st.markdown("### 新しい画像をアップロード（任意）")
image_main = st.file_uploader("メイン画像", type=["jpg", "jpeg", "png"])
image_sub1 = st.file_uploader("サブ画像1", type=["jpg", "jpeg", "png"])
image_sub2 = st.file_uploader("サブ画像2", type=["jpg", "jpeg", "png"])

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

    # 入力チェック
    if not name or not price or not desc:
        st.warning("商品名・価格・説明は必須です。")
        st.stop()

    # ----------------------------------------
    # ✨ 編集モード
    # ----------------------------------------
    if edit_mode:

        # 既存URLを保持
        main_url = edit_item["画像URL"]
        sub1_url = edit_item.get("画像URLサブ1", "")
        sub2_url = edit_item.get("画像URLサブ2", "")

        # 新しい画像があれば差し替え
        if image_main:
            main_url = process_and_upload(image_main)
        if image_sub1:
            sub1_url = process_and_upload(image_sub1)
        if image_sub2:
            sub2_url = process_and_upload(image_sub2)

        # 該当行を検索
        all_data = sheet.get_all_records()
        row_index = next((i for i, row in enumerate(all_data)
                          if row.get("商品ID") == edit_item["商品ID"]), None)

        if row_index is None:
            st.error("商品が見つかりませんでした。")
            st.stop()

        # 行番号（シートは1行目がヘッダー）
        row_num = row_index + 2

        # 更新データ
        update_row = [
            edit_item["商品ID"], name, price, desc, condition,
            main_url, sub1_url, sub2_url,
            edit_item["出品者ID"], edit_item["出品者名"],
            edit_item["投稿日時"], category,
            edit_item.get("購入者ID", ""), edit_item.get("購入者名", ""),
            edit_item.get("購入日時", ""), edit_item["ステータス"]
        ]

        # 更新
        sheet.update(f"A{row_num}:P{row_num}", [update_row])

        st.success("商品情報を更新しました！")
        st.session_state.pop("edit_product")
        st.switch_page("pages/7_マイページ（出品）.py")
        st.stop()

    # ----------------------------------------
    # ✨ 新規出品
    # ----------------------------------------
    else:
        if not image_main:
            st.warning("メイン画像は必須です。")
            st.stop()

        main_url = process_and_upload(image_main)
        sub1_url = process_and_upload(image_sub1) if image_sub1 else ""
        sub2_url = process_and_upload(image_sub2) if image_sub2 else ""

        product_id = str(uuid.uuid4())
        jst = pytz.timezone("Asia/Tokyo")
        now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

        new_row = [
            product_id, name, price, desc, condition,
            main_url, sub1_url, sub2_url,
            st.session_state["id"], st.session_state["username"],
            now, category,
            "", "", "", "出品中"
        ]

        sheet.append_row(new_row)
        st.success("商品を出品しました！")
        st.rerun()

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