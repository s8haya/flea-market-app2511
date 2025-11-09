import streamlit as st
import gspread
import json
import requests
from PIL import Image, UnidentifiedImageError
import io
from google.oauth2.credentials import Credentials

# 共通ヘッダー（ログイン状態とログアウト）
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.sidebar.markdown(f"👤 ログイン中：{st.session_state['username']} さん")
    if st.sidebar.button("ログアウト"):
        st.session_state["logged_in"] = False
        st.session_state.pop("id", None)
        st.session_state.pop("username", None)
        st.rerun()
else:
    st.warning("ログインしてください")
    st.stop()

# OAuth認証
try:
    creds_dict = json.loads(st.secrets["OAUTH_TOKEN"])
    creds = Credentials.from_authorized_user_info(creds_dict)
    gc = gspread.authorize(creds)
    sheet = gc.open(st.secrets["PRODUCT_SHEET_NAME"]).sheet1
except Exception as e:
    st.error(f"Google Sheetsの認証に失敗しました: {e}")
    st.stop()

# データ取得
try:
    data = sheet.get_all_records()
except Exception as e:
    st.error(f"商品データの取得に失敗しました: {e}")
    st.stop()

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
                    except UnidentifiedImageError:
                        st.warning("画像の読み込みに失敗しました。")
                        st.caption(f"画像URL: {image_url}")
                    except Exception:
                        st.warning("画像の取得に失敗しました。")
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