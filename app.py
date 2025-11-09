import streamlit as st
import pandas as pd

# CSVファイルの絶対パス（Google Drive上）
csv_path = "/content/drive/MyDrive/Colab Notebooks/flea_market_app/users.csv"

# CSVを文字コードと型指定で読み込む
try:
    df = pd.read_csv(csv_path, encoding="cp932", dtype=str)
except Exception as e:
    st.error(f"CSV読み込みエラー: {e}")
    st.stop()

# IDをキーにした辞書を作成
user_dict = {
    row["id"].strip(): {
        "password": row["password"].strip(),
        "username": row["username"].strip()
    }
    for _, row in df.iterrows()
}

# Streamlit画面設定
st.set_page_config(page_title="ログイン", layout="centered")
st.title("ログイン画面")

# サイドバーにログイン状態を表示（ログイン済みなら）
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.sidebar.markdown(f"👤 ログイン中：{st.session_state['username']} さん")
    if st.sidebar.button("ログアウト"):
        st.session_state["logged_in"] = False
        st.session_state.pop("id", None)
        st.session_state.pop("username", None)
        st.rerun()  # ページを再読み込みしてログイン画面に戻す

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
            st.rerun()  # ログイン後にページを再読み込み
        else:
            st.error("パスワードが間違っています")
    else:
        st.error("ユーザーIDが存在しません")

# ログイン後のユーザー名表示（本文側にも）
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.markdown("---")
    st.subheader(f"現在ログイン中：{st.session_state['username']} さん")