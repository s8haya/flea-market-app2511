import streamlit as st
import gspread
import json
from PIL import Image
from datetime import datetime
from google.oauth2.credentials import Credentials
import pytz
import time

st.set_page_config(page_title="支払い画面", layout="centered")
st.title("支払い画面")

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

# ✅ 商品情報の取得
product = st.session_state.get("selected_product")
if not product:
    st.warning("商品情報が見つかりませんでした。")
    st.switch_page("pages/2_商品検索.py")
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

# ✅ 商品情報表示
st.subheader("購入商品情報")
st.markdown(f"**{product.get('商品名', '不明')}**")
st.write(f"価格: {product.get('価格', '不明')}円")
st.write(f"カテゴリ: {product.get('カテゴリ', '不明')}")
st.write(product.get("説明", ""))
st.caption(f"出品者: {product.get('出品者名', '不明')} / 投稿日: {product.get('投稿日時', '不明')}")
st.caption(f"ステータス: {product.get('ステータス', '不明')}")

st.divider()
st.subheader("以下のQRコードからお支払いください")

# ✅ QRコード表示
try:
    qr_image = Image.open("QRhaya.png")
    st.image(qr_image, width=240)
except Exception:
    st.error("QRコード画像の読み込みに失敗しました。QRhaya.png が正しく配置されているか確認してください。")
    st.stop()

st.divider()
st.subheader("支払い後の操作")

# ✅ 支払い済処理
if st.button("支払い済"):
    try:
        product_id = product.get("商品ID")
        all_data = sheet.get_all_records()
        row_index = next((i for i, row in enumerate(all_data) if row.get("商品ID") == product_id), None)
        if row_index is None:
            st.error("商品が見つかりませんでした。")
            st.stop()

        current_status = all_data[row_index].get("ステータス", "")
        if current_status != "購入手続き中":
            st.warning("現在のステータスでは支払い処理を受け付けられません。")
            st.stop()

        sheet.update_cell(row_index + 2, 13, "支払い確認中")  # M列: ステータス
        time.sleep(1)
        st.success("購入ありがとうございました。出品者にお声かけの上、個人間で商品譲渡の対応をお願いします。")
    except Exception as e:
        st.error(f"ステータス更新に失敗しました: {e}")

# ✅ あとで支払う処理
if st.button("あとで支払う"):
    st.info("マイページから後ほどお支払いください。")
    st.switch_page("pages/6_マイページ（購入）.py")
    st.stop()

# ✅ フッターメニュー（共通4画面）
st.divider()
st.markdown("### 📌 メニュー")
with st.container(horizontal=True):
    st.page_link("pages/2_商品検索.py", label="商品検索")
    st.page_link("pages/3_出品画面.py", label="出品画面")
    st.page_link("pages/7_マイページ（出品）.py", label="マイページ（出品）")
    st.page_link("pages/6_マイページ（購入）.py", label="マイページ（購入）")