import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import gspread
from PIL import Image, UnidentifiedImageError
from datetime import datetime
import toml
import io
import pandas as pd
import pyheif

# ログインチェック
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("ログインしてください")
    st.stop()

# 設定読み込み
config = toml.load("/content/drive/MyDrive/Colab Notebooks/flea_market_app/config.toml")
token_path = config["google_sheets"]["credentials_path"]
sheet_name = config["google_sheets"]["spreadsheet_name"]
folder_id = config["google_drive"]["folder_id"]

# OAuth認証（Drive & Sheets共通）
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_authorized_user_file(token_path, SCOPES)
drive_service = build("drive", "v3", credentials=creds)
gc = gspread.authorize(creds)
sheet = gc.open(sheet_name).sheet1

# 出品者情報の読み込み
try:
    users_df = pd.read_csv("/content/drive/MyDrive/Colab Notebooks/flea_market_app/users.csv", encoding="cp932")
except UnicodeDecodeError:
    st.error("users.csv の文字コードが不正です。Shift_JIS または UTF-8 に変換してください。")
    st.stop()
except FileNotFoundError:
    st.error("users.csv が見つかりません。ファイルの場所を確認してください。")
    st.stop()

user_id = st.session_state.get("id", "")
username = users_df.loc[users_df["id"] == user_id, "username"].values[0] if user_id in users_df["id"].values else "不明"

# UI入力欄
st.title("商品投稿フォーム")
name = st.text_input("商品名")
price = st.number_input("価格", min_value=0)
desc = st.text_area("説明")
category = st.selectbox("カテゴリ", ["衣類", "雑貨", "本", "その他"])
image_file = st.file_uploader("商品画像をアップロード（jpg/png/heic形式）", type=["jpg", "jpeg", "png", "heic"])
submit = st.button("投稿する")

# 投稿処理
if submit:
    image_url = ""

    if image_file:
        try:
            # HEIC判定（拡張子またはMIMEタイプ）
            is_heic = image_file.name.lower().endswith(".heic") or "heic" in image_file.type.lower()

            if is_heic:
                file_bytes = image_file.read()
                heif_data = pyheif.read(file_bytes)
                img = Image.frombytes(
                    heif_data.mode,
                    heif_data.size,
                    heif_data.data,
                    "raw"
                )
            else:
                img = Image.open(image_file)

        except Exception:
            st.error("画像の読み込みに失敗しました。jpg/png/heic形式で再アップロードしてください。")
            st.stop()

        max_width = 512
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size)

        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

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

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = [None, name, price, desc, image_url, user_id, username, now, category]
    sheet.append_row(new_row)
    st.success("商品を投稿しました！")