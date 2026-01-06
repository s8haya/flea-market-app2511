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
# 📄 購入履歴取得
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
# ⚠ 未支払い（購入手続き中）の商品チェック
# ============================================
pending_items = [
    item for item in purchased_items
    if item.get("ステータス") == "購入手続き中"
]

if pending_items:
    st.warning(
        f"⚠ 支払いが未完了の商品が **{len(pending_items)} 件** あります。\n"
        "下記対象商品を確認のうえ、支払い画面に進んでください。"
    )
    st.divider()

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
# 🎨 CSS（カード枠＋ギャラリー固定枠＋リッチボタン）
# ============================================
st.markdown("""
<style>
.product-card {
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 20px;
    background-color: #fafafa;
}

.image-box {
    width: 240px;
    height: 240px;
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

.pay-button {
    background-color: #4CAF50;
    color: white;
    padding: 10px 18px;
    border-radius: 8px;
    border: none;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
}
.pay-button:hover {
    background-color: #3e8e41;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# 🖼️ 商品表示（ギャラリー＋カード枠）
# ============================================
if purchased_items:
    st.subheader("購入した商品一覧")

    for item in purchased_items:
        product_id = item.get("商品ID", "noid")

        main_url = item.get("画像URL", "")
        sub1_url = item.get("画像URLサブ1", "")
        sub2_url = item.get("画像URLサブ2", "")

        image_candidates = [url for url in [main_url, sub1_url, sub2_url] if url]

        # 初期表示
        if f"mypage_gallery_{product_id}" not in st.session_state:
            st.session_state[f"mypage_gallery_{product_id}"] = image_candidates[0] if image_candidates else ""

        current_img = st.session_state[f"mypage_gallery_{product_id}"]

        # カード開始
        st.markdown('<div class="product-card">', unsafe_allow_html=True)

        # メイン画像
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

        # サムネイル
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
                if st.button(f"{idx+1}", key=f"mypage_thumb_{product_id}_{idx}"):
                    st.session_state[f"mypage_gallery_{product_id}"] = url

        # 商品情報（出品者情報は表示OK）
        st.markdown(f"**{item.get('商品名', '不明')}**")
        st.markdown(f"**{item.get('価格', '不明')}円**")
        st.caption(f"カテゴリ: {item.get('カテゴリ', '不明')}")
        st.caption(f"状態: {item.get('状態', '不明')}")
        st.caption(f"出品者: {item.get('出品者名', '不明')}")
        st.caption(f"購入日時: {item.get('購入日時', '不明')}")
        st.caption(f"ステータス: {item.get('ステータス', '不明')}")

        # 支払い画面へ
        if item.get("ステータス") == "購入手続き中":
            if st.button("支払い画面へ進む", key=f"pay_{product_id}"):
                st.session_state["selected_product"] = item
                st.switch_page("pages/5_支払い画面.py")
                st.stop()

        st.markdown('</div>', unsafe_allow_html=True)

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