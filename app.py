import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.credentials import Credentials

st.set_page_config(page_title="ログイン画面", layout="centered")
st.title("ログイン画面")

# ✅ OAuth認証（分離＋例外処理）
try:
    creds_dict = json.loads(st.secrets["OAUTH_TOKEN"])
    creds = Credentials.from_authorized_user_info(creds_dict)
    gc = gspread.authorize(creds)
except Exception as e:
    st.error(f"Google Sheetsの認証に失敗しました: {e}")
    st.stop()

# ✅ ユーザー情報取得（キャッシュ化）
@st.cache_data(ttl=30)
def load_user_data():
    try:
        sheet = gc.open(st.secrets["USER_SHEET_NAME"]).sheet1
        records = sheet.get_all_records()
        return pd.DataFrame(records, dtype=str)
    except Exception as e:
        st.error(f"ユーザー情報の取得に失敗しました: {e}")
        return pd.DataFrame()

df = load_user_data()
if df.empty:
    st.stop()

# ✅ ユーザー辞書構築
user_dict = {
    row["id"].strip(): {
        "password": row["password"].strip(),
        "username": row["username"].strip()
    }
    for _, row in df.iterrows()
}

# ✅ ログイン状態の分岐
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    with st.container(horizontal=True):
        st.markdown(f"👤 ログイン中：**{st.session_state['username']}** さん")
        if st.button("ログアウト"):
            st.session_state["logged_in"] = False
            st.session_state.pop("id", None)
            st.session_state.pop("username", None)
            st.rerun()
    st.divider()
    st.subheader("下のメニューから画面を選択してください。")

else:
    with st.container():
        input_id = st.text_input("ユーザーID").strip()
        input_pass = st.text_input("パスワード", type="password").strip()
        login_btn = st.button("ログイン")

    if login_btn:
        if input_id in user_dict:
            expected_pw = user_dict[input_id]["password"]
            if input_pass == expected_pw:
                st.session_state["logged_in"] = True
                st.session_state["id"] = input_id
                st.session_state["username"] = user_dict[input_id]["username"]
                st.success(f"{user_dict[input_id]['username']}さん、ようこそ！")
                st.rerun()
            else:
                st.error("パスワードが間違っています")
        else:
            st.error("ユーザーIDが存在しません")

# ✅ フッターメニュー
st.divider()
st.markdown("### 📌 メニュー")
with st.container(horizontal=True):
    st.page_link("app.py", label="ログイン画面")
    st.page_link("pages/2_商品検索.py", label="商品検索")
    st.page_link("pages/3_出品画面.py", label="出品画面")