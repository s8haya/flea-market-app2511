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

# ログインチェック＋ヘッダー
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    with st.container():
        cols = st.columns([3, 1])
        with cols[0]:
            st.markdown(f"👤 ログイン中：**{st.session_state['username']}** さん")
        with cols[1]:
            if st.button("ログアウト"):
                st.session_state["logged_in"] = False
                st.session_state.pop("id", None)
                st.session_state.pop("username", None)
                st.rerun()
else:
    st.warning("ログインしてください")
    st.stop()

st.title("商品投稿フォーム")

# OAuth認証
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

# ユーザー情報
user_id = st.session_state.get("id", "")
username = st.session_state.get("username", "不明")

# 入力欄
name = st.text_input("商品名")
price = st.number_input("価格", min_value=0)
desc = st.text_area("説明")
category = st.selectbox("カテゴリ", ["衣類", "雑貨", "本", "その他"])
image_file = st.file_uploader("商品画像をアップロード（jpg/png形式）", type=["jpg", "jpeg", "png", "heic"])
submit = st.button("投稿する")

# 投稿処理
if submit:
    image_url = ""

    if image_file:
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

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = [None, name, price, desc, image_url, user_id, username, now, category]
    try:
        sheet.append_row(new_row)
        st.success("商品を投稿しました！")
    except Exception as e:
        st.error(f"商品情報の登録に失敗しました: {e}")

# フッターメニュー
st.markdown("---")
st.markdown("### 📌 メニュー")
menu_cols = st.columns(3)
with menu_cols[0]:
    st.page_link("app.py", label="ログイン画面")
with menu_cols[1]:
    st.page_link("pages/2_商品検索.py", label="商品検索")
with menu_cols[2]:
    st.page_link("pages/3_出品画面.py", label="出品画面")