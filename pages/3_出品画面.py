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

# ✅ ログインチェック＋ヘッダー
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

# ✅ 投稿完了後のメッセージと遷移ボタン
if st.session_state.get("posted"):
    st.success("商品を出品しました！")
    if st.button("マイページ（出品）へ移動"):
        st.session_state.pop("posted")
        st.switch_page("pages/7_マイページ（出品）.py")
    st.stop()

# ✅ OAuth認証（Sheetsのみ）
try:
    creds_dict = json.loads(st.secrets["OAUTH_TOKEN"])
    creds = Credentials.from_authorized_user_info(creds_dict)
    gc = gspread.authorize(creds)
    sheet = gc.open(st.secrets["PRODUCT_SHEET_NAME"]).sheet1
except Exception as e:
    st.error(f"Google Sheetsの認証に失敗しました: {e}")
    st.stop()

# ✅ Cloudinary認証
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)

# ✅ ユーザー情報
user_id = st.session_state.get("id", "")
username = st.session_state.get("username", "不明")

# ✅ 入力フォーム（順番整理済み）
name = st.text_input("商品名")
price = st.number_input("価格", min_value=0)
category = st.selectbox("カテゴリ", ["衣類", "雑貨", "日用品", "本", "スポーツ", "その他"])
condition = st.selectbox("状態", ["新品", "中古"])
desc = st.text_area("説明")
image_file = st.file_uploader("商品画像をアップロード（jpg/png形式）", type=["jpg", "jpeg", "png"])
submit = st.button("出品する")

# ✅ 投稿処理
if submit:
    if not name or not price or not desc or not image_file:
        st.warning("商品名・価格・説明・画像はすべて必須です。")
        st.stop()

    try:
        img = Image.open(image_file)
        img = ImageOps.exif_transpose(img)
    except UnidentifiedImageError:
        st.error("画像の読み込みに失敗しました。jpg/png形式で再アップロードしてください。")
        st.stop()

    max_width = 512
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size)

    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    # ✅ Cloudinaryにアップロード
    try:
        result = cloudinary.uploader.upload(img_buffer, folder="products")
        image_url = result["secure_url"]
    except Exception as e:
        st.error(f"Cloudinaryへの画像アップロードに失敗しました: {e}")
        st.stop()

    # ✅ 商品情報の登録（状態列を追加）
    product_id = str(uuid.uuid4())
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    status = "出品中"

    new_row = [
        product_id, name, price, desc, condition, image_url,
        user_id, username, now, category,
        "", "", "", status
    ]

    try:
        sheet.append_row(new_row)
        time.sleep(1)
        st.session_state["posted"] = True
        st.rerun()
    except Exception as e:
        st.error(f"商品情報の登録に失敗しました: {e}")

# ✅ フッターメニュー（共通4画面）
st.divider()
st.markdown("### 📌 メニュー")
with st.container(horizontal=True):
    st.page_link("pages/2_商品検索.py", label="商品検索")
    st.page_link("pages/3_出品画面.py", label="出品画面")
    st.page_link("pages/7_マイページ（出品）.py", label="マイページ（出品）")
    st.page_link("pages/6_マイページ（購入）.py", label="マイページ（購入）")