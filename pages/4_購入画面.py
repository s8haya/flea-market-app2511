import streamlit as st
import gspread
import json
import requests
from PIL import Image, UnidentifiedImageError
import io
from datetime import datetime
from google.oauth2.credentials import Credentials
import pytz

st.set_page_config(page_title="購入確認", layout="centered")

# ログインチェック＋ヘッダー
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

st.title("購入確認")

# 商品情報の取得
product = st.session_state.get("selected_product")
if not product:
    st.warning("商品情報が見つかりませんでした。")
    st.switch_page("pages/2_商品検索.py")
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

# 商品表示
image_url = product.get("画像URL", "")
if image_url:
    try:
        response = requests.get(image_url)
        img = Image.open(io.BytesIO(response.content))
        st.image(img, width=240)
    except Exception:
        st.warning("画像の読み込みに失敗しました。")
        st.caption(f"画像URL: {image_url}")
else:
    st.write("画像なし")

st.markdown(f"### {product.get('商品名', '不明')}")
st.write(f"価格: {product.get('価格', '不明')}円")
st.write(f"カテゴリ: {product.get('カテゴリ', '不明')}")
st.write(product.get("説明", ""))
st.caption(f"出品者: {product.get('出品者名', '不明')} / 投稿日: {product.get('投稿日時', '不明')}")
st.caption(f"ステータス: {product.get('ステータス', '不明')}")

st.divider()
st.subheader("本当に購入しますか？")

# 購入処理
if st.button("購入する"):
    try:
        product_id = product.get("商品ID")
        all_data = sheet.get_all_records()
        row_index = next((i for i, row in enumerate(all_data) if row.get("商品ID") == product_id), None)
        if row_index is None:
            st.error("商品が見つかりませんでした。")
            st.stop()

        current_row = all_data[row_index]
        current_status = current_row.get("ステータス", "")
        current_buyer_id = str(current_row.get("購入者", "")).strip()
        current_user_id = str(st.session_state.get("id", "")).strip()

        # ✅ 許可条件：出品中 or 自分が購入者
        if current_status == "出品中":
            jst = pytz.timezone("Asia/Tokyo")
            now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

            sheet.update_cell(row_index + 2, 10, current_user_id)                     # J列: 購入者
            sheet.update_cell(row_index + 2, 11, st.session_state.get("username", "")) # K列: 購入者名
            sheet.update_cell(row_index + 2, 12, now)                                  # L列: 購入日時
            sheet.update_cell(row_index + 2, 13, "購入手続き中")                        # M列: ステータス

            st.success("購入手続きに進みます")
            st.switch_page("pages/5_支払い画面.py")

        elif current_buyer_id == current_user_id:
            st.success("購入済みの商品です。支払い画面に進みます")
            st.switch_page("pages/5_支払い画面.py")

        else:
            st.error("ほかの方がすでに購入されたか、商品が取下げられた可能性があります。商品検索画面にお戻りください。")
            st.stop()

    except Exception as e:
        st.error("ほかの方がすでに購入されたか、商品が取下げられた可能性があります。商品検索画面にお戻りください。")

# キャンセル処理
if st.button("キャンセルする"):
    try:
        product_id = product.get("商品ID")
        all_data = sheet.get_all_records()
        row_index = next((i for i, row in enumerate(all_data) if row.get("商品ID") == product_id), None)
        if row_index is None:
            st.error("商品が見つかりませんでした。")
            st.stop()

        current_status = all_data[row_index].get("ステータス", "")
        if current_status in ["出品中", "取下げ"]:
            st.switch_page("pages/2_商品検索.py")
        else:
            st.warning("すでに商品が購入された等の状態です。自身が購入しキャンセルしたい場合は、照会先に連絡ください。そのほかの方は下メニューから商品検索画面にお戻りください。")
    except Exception as e:
        st.error("キャンセル処理中にエラーが発生しました。")

# フッターメニュー
st.divider()
st.markdown("### 📌 メニュー")
with st.container(horizontal=True):
    st.page_link("app.py", label="ログイン画面")
    st.page_link("pages/2_商品検索.py", label="商品検索")
    st.page_link("pages/3_出品画面.py", label="出品画面")