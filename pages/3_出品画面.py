import streamlit as st
import pandas as pd
import gspread
import json
from PIL import Image, UnidentifiedImageError
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
import io
import uuid
import pytz
import time

st.set_page_config(page_title="出品画面", layout="centered")
st.title("商品投稿フォーム")

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

# ✅ OAuth認証とサービス初期化
try:
    creds_dict = json.loads(st.secrets["OAUTH_TOKEN"])
    creds = Credentials.from_authorized_user_info(creds_dict)
    gc = gspread.authorize(creds)
    sheet = gc.open(st.secrets["PRODUCT_SHEET_NAME"]).sheet1
    folder_id = st.secrets["DRIVE_FOLDER_ID"]
    drive_service = build("drive", "v3", credentials=creds)
except Exception as e:
    st.error(f"Google SheetsまたはDriveの認証に失敗しました: {e}")
    st.stop()

# ✅ ユーザー情報
user_id = st.session_state.get("id", "")
username = st.session_state.get("username", "不明")

# ✅ 入力フォーム
name = st.text_input("商品名")
price = st.number_input("価格", min_value=0)
desc = st.text_area("説明")
category = st.selectbox("カテゴリ", ["衣類", "雑貨", "本", "その他"])
image_file = st.file_uploader("商品画像をアップロード（jpg/png形式）", type=["jpg", "jpeg", "png", "heic"])
submit = st.button("投稿する")

# ✅ 投稿処理
if submit:
    if not name or not price or not desc or not image_file:
        st.warning("商品名・価格・説明・画像はすべて必須です。")
        st.stop()

    if image_file.name.lower().endswith(".heic"):
        st.error("HEIC形式の画像は現在サポートされていません。JPEGまたはPNG形式でアップロードしてください。")
        st.stop()

    try:
        img = Image.open(image_file)
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

    # ✅ 画像アップロード
    try:
        file_metadata = {
            "name": image_file.name,
            "parents": [folder_id]
        }
        media = MediaIoBaseUpload(img_buffer, mimetype="image/png")
        uploaded = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()

        drive_service.permissions().create(
            fileId=uploaded["id"],
            body={"role": "reader", "type": "anyone"},
        ).execute()

        image_url = f"https://drive.google.com/uc?export=view&id={uploaded['id']}"
    except Exception as e:
        st.error(f"画像のアップロードに失敗しました: {e}")
        st.stop()

    # ✅ 商品情報の登録
    product_id = str(uuid.uuid4())
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")
    status = "出品中"

    new_row = [
        product_id, name, price, desc, image_url,
        user_id, username, now, category,
        "", "", "", status
    ]

    try:
        sheet.append_row(new_row)
        time.sleep(1)
        st.success("商品を投稿しました！")
    except Exception as e:
        st.error(f"商品情報の登録に失敗しました: {e}")

# ✅ フッターメニュー（リンク専用）
st.divider()
st.markdown("### 📌 メニュー")
with st.container(horizontal=True):
    st.page_link("app.py", label="ログイン画面")
    st.page_link("pages/2_商品検索.py", label="商品検索")
    st.page_link("pages/3_出品画面.py", label="出品画面")