import streamlit as st
import gspread
import json
import requests
from PIL import Image
import io
from google.oauth2.credentials import Credentials

st.set_page_config(page_title="マイページ（購入）", layout="centered")
st.title("マイページ（購入）")

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

# ✅ OAuth認証
try:
    creds_dict = json.loads(st.secrets["OAUTH_TOKEN"])
    creds = Credentials.from_authorized_user_info(creds_dict)
    gc = gspread.authorize(creds)
    sheet = gc.open(st.secrets["PRODUCT_SHEET_NAME"]).sheet1
except Exception as e:
    st.error(f"Google Sheetsの認証に失敗しました: {e}")
    st.stop()

# ✅ 商品データ取得
try:
    raw_data = sheet.get_all_records()
    user_id = str(st.session_state.get("id", "")).strip()
    purchased_items = [row for row in raw_data if str(row.get("購入者", "")).strip() == user_id]
except Exception as e:
    st.error(f"購入履歴の取得に失敗しました: {e}")
    st.stop()

# ✅ 商品表示
if purchased_items:
    st.subheader("購入した商品一覧")
    for item in purchased_items:
        with st.container(border=True):
            image_url = item.get("画像URL", "")
            if image_url:
                try:
                    response = requests.get(image_url)
                    img = Image.open(io.BytesIO(response.content))
                    st.image(img, width=160)
                except Exception:
                    st.caption(f"画像読み込み失敗: {image_url}")
            else:
                st.write("画像なし")

            st.markdown(f"**{item.get('商品名', '不明')}**")
            st.caption(f"{item.get('価格', '不明')}円 / {item.get('カテゴリ', '不明')}")
            st.caption(f"出品者: {item.get('出品者名', '不明')} / 投稿日: {item.get('投稿日時', '不明')}")
            st.caption(f"ステータス: {item.get('ステータス', '不明')}")

            if item.get("ステータス") == "購入手続き中":
                if st.button("支払い画面へ進む", key=f"pay_{item.get('商品ID')}"):
                    st.session_state["selected_product"] = item
                    st.switch_page("pages/5_支払い画面.py")
                    st.stop()
else:
    st.info("購入履歴がありません。")

# ✅ フッターメニュー（リンク専用）
st.divider()
st.markdown("### 📌 メニュー")
with st.container(horizontal=True):
    st.page_link("app.py", label="ログイン画面")
    st.page_link("pages/2_商品検索.py", label="商品検索")
    st.page_link("pages/3_出品画面.py", label="出品画面")
    st.page_link("pages/7_マイページ（出品）.py", label="マイページ（出品）")