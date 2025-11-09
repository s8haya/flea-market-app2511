import streamlit as st
import gspread
from google.oauth2.credentials import Credentials
import toml
import requests
from PIL import Image
import io
import pandas as pd

# ログインチェック
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("ログインしてください")
    st.stop()

# 設定読み込み
config = toml.load("/content/drive/MyDrive/Colab Notebooks/flea_market_app/config.toml")
token_path = config["google_sheets"]["credentials_path"]
sheet_name = config["google_sheets"]["spreadsheet_name"]

# OAuth認証（Driveスコープも追加）
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_authorized_user_file(token_path, SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open(sheet_name).sheet1

# データ取得
data = sheet.get_all_records()

# UI
st.title("商品検索")
search = st.text_input("商品名で検索")

# 検索フィルタ
filtered = [item for item in data if search.lower() in item.get("商品名", "").lower()] if search else data

# 一覧表示
if filtered:
    for item in filtered:
        with st.container():
            cols = st.columns([1, 2])
            with cols[0]:
                image_url = item.get("画像URL", "")
                if image_url:
                    try:
                        response = requests.get(image_url)
                        img = Image.open(io.BytesIO(response.content))
                        st.image(img, width=150)
                    except Exception:
                        st.warning("画像の読み込みに失敗しました。")
                        st.caption(f"画像URL: {image_url}")
                else:
                    st.write("画像なし")
            with cols[1]:
                st.subheader(item.get("商品名", "不明"))
                st.write(f"価格: {item.get('価格', '不明')}円")
                st.write(f"カテゴリ: {item.get('カテゴリ', '不明')}")
                st.write(item.get("説明", ""))
                st.caption(f"出品者: {item.get('出品者名', '不明')} / 投稿日: {item.get('投稿日時', '不明')}")
else:
    st.warning("該当する商品が見つかりませんでした。")