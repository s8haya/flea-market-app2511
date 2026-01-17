import streamlit as st
import gspread
import json
import pandas as pd
from google.oauth2.credentials import Credentials

st.set_page_config(page_title="部署別の売買状況", layout="wide")
st.title("📊 部署別の売買状況ダッシュボード")

# ============================================
# 🔐 ログインチェック
# ============================================
if not st.session_state.get("logged_in"):
    st.warning("ログインしてください")
    if st.button("ログイン画面へ"):
        st.switch_page("app.py")
    st.stop()

st.markdown(f"👤 ログイン中：**{st.session_state['username']}** さん")

# ============================================
# 🔑 OAuth認証
# ============================================
try:
    creds_dict = json.loads(st.secrets["OAUTH_TOKEN"])
    creds = Credentials.from_authorized_user_info(creds_dict)
    gc = gspread.authorize(creds)

    # 商品一覧
    product_sheet = gc.open(st.secrets["PRODUCT_SHEET_NAME"]).sheet1
    product_data = product_sheet.get_all_records()

    # users（department_big を含む）
    users_sheet = gc.open(st.secrets["USER_SHEET_NAME"]).sheet1
    users_data = users_sheet.get_all_records()

except Exception as e:
    st.error(f"Google Sheetsの認証に失敗しました: {e}")
    st.stop()

# ============================================
# 🧩 データ整形
# ============================================
df_products = pd.DataFrame(product_data)
df_users = pd.DataFrame(users_data)

# ID を文字列化
df_products["出品者"] = df_products["出品者"].astype(str)
df_products["購入者"] = df_products["購入者"].astype(str)
df_users["id"] = df_users["id"].astype(str)

# users を JOIN（出品者側）
df_products = df_products.merge(
    df_users[["id", "department_big"]],
    left_on="出品者",
    right_on="id",
    how="left"
).rename(columns={"department_big": "出品者部署"})

# users を JOIN（購入者側）
df_products = df_products.merge(
    df_users[["id", "department_big"]],
    left_on="購入者",
    right_on="id",
    how="left"
).rename(columns={"department_big": "購入者部署"})

# ============================================
# 📊 部署別集計
# ============================================
dept_list = sorted(df_users["department_big"].unique())

summary = []

for dept in dept_list:
    # 出品数
    sell_count = len(df_products[df_products["出品者部署"] == dept])

    # 購入数
    buy_count = len(df_products[df_products["購入者部署"] == dept])

    # 累計出品金額
    sell_amount = df_products[df_products["出品者部署"] == dept]["価格"].sum()

    # 累計購入金額
    buy_amount = df_products[df_products["購入者部署"] == dept]["価格"].sum()

    # 参加人数（出品 or 購入した人）
    sellers = set(df_products[df_products["出品者部署"] == dept]["出品者"])
    buyers = set(df_products[df_products["購入者部署"] == dept]["購入者"])
    participants = len(sellers.union(buyers))

    summary.append({
        "部署": dept,
        "出品数": sell_count,
        "購入数": buy_count,
        "累計出品金額": sell_amount,
        "累計購入金額": buy_amount,
        "参加人数": participants
    })

df_summary = pd.DataFrame(summary)

# ============================================
# 🏆 ランキング表示（競争心を刺激）
# ============================================
st.subheader("🏆 部署別ランキング")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🔥 出品数ランキング")
    st.dataframe(df_summary.sort_values("出品数", ascending=False), use_container_width=True)

with col2:
    st.markdown("### 💰 購入数ランキング")
    st.dataframe(df_summary.sort_values("購入数", ascending=False), use_container_width=True)

# ============================================
# 📈 ダッシュボード（全体サマリー）
# ============================================
st.subheader("📈 部署別サマリー")

st.dataframe(df_summary, use_container_width=True)

# ============================================
# 📌 フッターメニュー
# ============================================
st.divider()
st.markdown("### 📌 メニュー")
with st.container():
    st.page_link("pages/2_商品検索.py", label="商品検索")
    st.page_link("pages/3_出品画面.py", label="出品画面")
    st.page_link("pages/7_マイページ（出品）.py", label="マイページ（出品）")
    st.page_link("pages/6_マイページ（購入）.py", label="マイページ（購入）")