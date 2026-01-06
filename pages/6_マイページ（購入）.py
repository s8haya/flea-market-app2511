import streamlit as st
import gspread
import json
from google.oauth2.credentials import Credentials
from datetime import datetime

st.set_page_config(page_title="マイページ（購入）", layout="centered")
st.title("マイページ（購入）")

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
# 📄 購入履歴データ取得
# ============================================
try:
    raw_data = sheet.get_all_records()
    user_id = str(st.session_state.get("id", "")).strip()
    purchased_items = [
        row for row in raw_data
        if str(row.get("購入者", "")).strip() == user_id
    ]
except Exception as e:
    st.error(f"購入履歴の取得に失敗しました: {e}")
    st.stop()

# ============================================
# 🕒 購入日時で新しい順にソート
# ============================================
def parse_dt(dt):
    try:
        return datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    except:
        return datetime.min

purchased_items.sort(key=lambda x: parse_dt(x.get("購入日時", "")), reverse=True)

# ============================================
# 🖼️ 商品表示（Cloudinary対応）
# ============================================
if purchased_items:
    st.subheader("購入した商品一覧")

    for item in purchased_items:
        with st.container(border=True):

            # Cloudinary画像を高速表示
            image_url = item.get("画像URL", "")
            if image_url:
                st.image(image_url, width=160)
            else:
                st.write("画像なし")

            # 商品情報
            st.markdown(f"**{item.get('商品名', '不明')}**")
            st.caption(f"{item.get('価格', '不明')}円 / {item.get('カテゴリ', '不明')}")
            st.caption(f"出品者: {item.get('出品者名', '不明')} / 投稿日: {item.get('投稿日時', '不明')}")
            st.caption(f"購入日時: {item.get('購入日時', '不明')}")
            st.caption(f"ステータス: {item.get('ステータス', '不明')}")

            # 支払い画面へ
            if item.get("ステータス") == "購入手続き中":
                if st.button("支払い画面へ進む", key=f"pay_{item.get('商品ID')}"):
                    st.session_state["selected_product"] = item
                    st.switch_page("pages/5_支払い画面.py")
                    st.stop()

else:
    st.info("購入履歴がありません。")

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