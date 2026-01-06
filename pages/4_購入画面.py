import streamlit as st
import gspread
import json
from PIL import Image, UnidentifiedImageError
import io
from datetime import datetime
from google.oauth2.credentials import Credentials
import pytz
import time

st.set_page_config(page_title="購入確認", layout="centered")
st.title("購入確認画面")

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
# 📦 商品情報の取得（初期）
# ============================================
product = st.session_state.get("selected_product")
if not product:
    st.warning("商品情報が見つかりませんでした。")
    st.switch_page("pages/2_商品検索.py")
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
# 🆕 商品情報を最新化（シートから再取得）
# ============================================
product_id = product.get("商品ID")
try:
    all_data = sheet.get_all_records()
    updated = next((row for row in all_data if row.get("商品ID") == product_id), None)
    if updated:
        st.session_state["selected_product"] = updated
        product = updated
except Exception:
    pass

# ============================================
# 🎨 CSS（ギャラリー固定枠）
# ============================================
st.markdown("""
<style>
.image-box {
    width: 260px;
    height: 260px;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 6px;
}
.image-box img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}
.thumb-box {
    width: 60px;
    height: 60px;
    overflow: hidden;
    border: 1px solid #ccc;
    margin-top: 4px;
}
.thumb-box img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# 🖼️ ギャラリー表示
# ============================================
main_url = product.get("画像URL", "")
sub1_url = product.get("画像URLサブ1", "")
sub2_url = product.get("画像URLサブ2", "")

image_candidates = [url for url in [main_url, sub1_url, sub2_url] if url]

product_id = product.get("商品ID", "noid")

if f"gallery_{product_id}" not in st.session_state:
    st.session_state[f"gallery_{product_id}"] = image_candidates[0] if image_candidates else ""

current_img = st.session_state[f"gallery_{product_id}"]

if current_img:
    st.markdown(
        f"""
        <div class="image-box">
            <img src="{current_img}" />
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.write("画像なし")

thumb_cols = st.columns(3)
thumb_urls = [main_url, sub1_url, sub2_url]

for idx, (col, url) in enumerate(zip(thumb_cols, thumb_urls)):
    if not url:
        continue
    with col:
        st.markdown(
            f"""
            <div class="thumb-box">
                <img src="{url}" />
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button(f"{idx+1}", key=f"thumbbtn_confirm_{product_id}_{idx}"):
            st.session_state[f"gallery_{product_id}"] = url

# ============================================
# 📄 商品情報（出品者情報は非表示）
# ============================================
st.markdown(f"### {product.get('商品名', '不明')}")
st.write(f"価格: {product.get('価格', '不明')}円")
st.write(f"カテゴリ: {product.get('カテゴリ', '不明')}")

desc_text = product.get("説明", "")
st.markdown(desc_text.replace("\n", "<br>"), unsafe_allow_html=True)

st.caption(f"出品日時: {product.get('投稿日時', '不明')}")
st.caption(f"ステータス: {product.get('ステータス', '不明')}")

st.divider()
st.subheader("本当に購入しますか？")

# ============================================
# 🛒 購入処理
# ============================================
if st.button("購入する", key="buy_main"):
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

        if current_status == "出品中":
            jst = pytz.timezone("Asia/Tokyo")
            now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

            sheet.update_cell(row_index + 2, 13, current_user_id)
            sheet.update_cell(row_index + 2, 14, st.session_state.get("username", ""))
            sheet.update_cell(row_index + 2, 15, now)
            sheet.update_cell(row_index + 2, 16, "購入手続き中")
            time.sleep(1)

            st.success("購入手続きに進みます")
            st.switch_page("pages/5_支払い画面.py")
            st.stop()

        elif current_buyer_id == current_user_id:
            st.success("購入済みの商品です。支払い画面に進みます")
            st.switch_page("pages/5_支払い画面.py")
            st.stop()

        else:
            st.error("ほかの方がすでに購入された可能性があります。")
            st.switch_page("pages/2_商品検索.py")
            st.stop()

    except Exception:
        st.error("購入処理中にエラーが発生しました。")
        st.switch_page("pages/2_商品検索.py")
        st.stop()

# ============================================
# ❌ キャンセル
# ============================================
if st.button("キャンセルする"):
    st.switch_page("pages/2_商品検索.py")
    st.stop()

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