import streamlit as st
import gspread
import json
import requests
from PIL import Image, UnidentifiedImageError
import io
from google.oauth2.credentials import Credentials

st.set_page_config(page_title="商品検索", layout="centered")

# ログインチェック＋ヘッダー（Flexbox風）
if "logged_in" in st.session_state and st.session_state["logged_in"]:
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

st.title("商品検索")

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

# 検索UI
search = st.text_input("商品名で検索")
filtered = [item for item in data if search.lower() in item.get("商品名", "").lower()] if search else data

# 商品表示（スマホ2列対応）
if filtered:
    num_cols = 2  # 1行に2商品
    for i in range(0, len(filtered), num_cols):
        row_items = filtered[i:i+num_cols]
        cols = st.columns(len(row_items))
        for col, item in zip(cols, row_items):
            with col:
                with st.container():
                    image_url = item.get("画像URL", "")
                    if image_url:
                        try:
                            response = requests.get(image_url)
                            img = Image.open(io.BytesIO(response.content))
                            img = img.resize((120, 120))  # ✅ サイズ統一
                            st.image(img)
                        except Exception:
                            st.warning("画像の読み込みに失敗しました。")
                            st.caption(f"画像URL: {image_url}")
                    else:
                        st.write("画像なし")

                    st.markdown(f"**{item.get('商品名', '不明')}**")
                    st.caption(f"{item.get('価格', '不明')}円 / {item.get('カテゴリ', '不明')}")
                    st.caption(f"{item.get('出品者名', '不明')} / {item.get('投稿日時', '不明')}")
else:
    st.warning("該当する商品が見つかりませんでした。")

# フッターメニュー（Flexbox風）
st.divider()
st.markdown("### 📌 メニュー")
with st.container(horizontal=True):
    st.page_link("app.py", label="ログイン画面")
    st.page_link("pages/2_商品検索.py", label="商品検索")
    st.page_link("pages/3_出品画面.py", label="出品画面")