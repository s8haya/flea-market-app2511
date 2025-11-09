import streamlit as st
import pandas as pd
import gspread
import json

# Streamlit画面設定
st.set_page_config(page_title="ログイン", layout="centered")
st.title("ログイン画面")

# Google Sheets認証（Secretsから読み込み）
try:
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    gc = gspread.service_account_from_dict(creds_dict)
    st.write("認証成功")

    sheet_name = st.secrets["USER_SHEET_NAME"]
    st.write(f"指定されたシート名: {sheet_name}")

    sheet = gc.open(sheet_name).sheet1
    st.write("シート取得成功")

    records = sheet.get_all_records()
    df = pd.DataFrame(records, dtype=str)
except Exception as e:
    st.error(f"Google Sheetsからユーザー情報の取得に失敗しました: {e}")
    st.stop()


# IDをキーにした辞書を作成
user_dict = {
    row["id"].strip(): {
        "password": row["password"].strip(),
        "username": row["username"].strip()
    }
    for _, row in df.iterrows()
}

# サイドバーにログイン状態を表示（ログイン済みなら）
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.sidebar.markdown(f"👤 ログイン中：{st.session_state['username']} さん")
    if st.sidebar.button("ログアウト"):
        st.session_state["logged_in"] = False
        st.session_state.pop("id", None)
        st.session_state.pop("username", None)
        st.rerun()

# 入力欄（空白除去）
input_id = st.text_input("ユーザーID").strip()
input_pass = st.text_input("パスワード", type="password").strip()
login_btn = st.button("ログイン")

# ログイン判定
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

# ログイン後のユーザー名表示と画像アップロード
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.markdown("---")
    st.subheader(f"現在ログイン中：{st.session_state['username']} さん")

    # 画像アップロード（HEIC検出）
    uploaded_file = st.file_uploader("画像をアップロード", type=["jpg", "jpeg", "png", "heic"])

    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(".heic"):
            st.error("HEIC形式の画像は現在サポートされていません。JPEGまたはPNG形式でアップロードしてください。")
            st.stop()
        else:
            st.success(f"{uploaded_file.name} を受け付けました！")