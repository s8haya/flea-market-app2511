import streamlit as st
import gspread
import json
from google.oauth2.credentials import Credentials
from datetime import datetime

st.set_page_config(page_title="商品検索", layout="centered")

# ============================================
# 🔐 ログインチェック
# ============================================
if st.session_state.get("logged_in"):
    with st.container():
        colA, colB = st.columns([4, 1])
        with colA:
            st.markdown(f"👤 ログイン中：**{st.session_state['username']}** さん")
        with colB:
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

# ============================================
# 🔑 OAuth認証（キャッシュ）
# ============================================
@st.cache_resource
def get_gspread_client():
    creds_dict = json.loads(st.secrets["OAUTH_TOKEN"])
    creds = Credentials.from_authorized_user_info(creds_dict)
    return gspread.authorize(creds)

gc = get_gspread_client()

# ============================================
# 📄 商品データ取得（キャッシュなし → 最新化）
# ============================================
def load_product_data():
    try:
        sheet = gc.open(st.secrets["PRODUCT_SHEET_NAME"]).sheet1
        raw_data = sheet.get_all_records()
        return [
            row for row in raw_data
            if row.get("商品名")
            and row.get("価格")
            and row.get("画像URL")
            and row.get("ステータス") != "取下げ"
        ]
    except Exception as e:
        st.error(f"商品データの取得に失敗しました: {e}")
        return []

data = load_product_data()
if not data:
    st.stop()

# ============================================
# 🎨 CSS（カード枠＋画像ラベル）
# ============================================
st.markdown("""
<style>
.product-card {
    border-bottom: 1px solid #ccc;
    padding-bottom: 12px;
    margin-bottom: 20px;
}

.image-overlay {
    position: relative;
    width: 100%;
    height: 200px;
    overflow: hidden;
    margin-bottom: 8px;
    background-color: #f9f9f9;
    display: flex;
    justify-content: center;
    align-items: center;
}
.image-overlay img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

.label {
    position: absolute;
    padding: 4px 8px;
    font-size: 13px;
    font-weight: bold;
    color: white;
    border-radius: 4px;
}
.label.condition {
    top: 8px;
    left: 8px;
    background-color: #4caf50;
}
.label.price {
    bottom: 8px;
    right: 8px;
    background-color: #ff6b6b;
}

.buy-button {
    background-color: #1976d2;
    color: white;
    padding: 8px 14px;
    border-radius: 6px;
    border: none;
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;
}
.buy-button:hover {
    background-color: #1565c0;
}
</style>
""", unsafe_allow_html=True)


# ============================================
# 🔍 検索・絞り込み UI
# ============================================
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("🔍 商品名で検索")
    with col2:
        category_filter = st.selectbox(
            "📦 カテゴリ絞り込み",
            ["すべて"] + sorted(set(row.get("カテゴリ", "") for row in data))
        )
    with col3:
        condition_filter = st.selectbox(
            "🧺 状態絞り込み",
            ["すべて"] + sorted(set(row.get("状態", "") for row in data))
        )

    col4, col5, col6 = st.columns(3)
    with col4:
        status_filter = st.selectbox(
            "📌 出品ステータス",
            ["すべて", "出品中のみ", "売却済"],
            index=1
        )
    with col5:
        sort_option = st.radio(
            "並び順",
            ["新着順", "価格が安い順", "価格が高い順"],
            horizontal=True
        )
    with col6:
        st.empty()

# ============================================
# 🔄 ページリセット（フィルター変更時）
# ============================================
if "prev_filters" not in st.session_state:
    st.session_state["prev_filters"] = {}

current_filters = {
    "search": search,
    "category": category_filter,
    "condition": condition_filter,
    "status": status_filter,
    "sort": sort_option
}

if st.session_state["prev_filters"] != current_filters:
    st.session_state["page"] = 1
    st.session_state["prev_filters"] = current_filters

# ============================================
# 🔎 絞り込み処理
# ============================================
filtered = data

if search:
    filtered = [
        item for item in filtered
        if search.lower() in item.get("商品名", "").lower()
    ]

if category_filter != "すべて":
    filtered = [item for item in filtered if item.get("カテゴリ") == category_filter]

if condition_filter != "すべて":
    filtered = [item for item in filtered if item.get("状態") == condition_filter]

if status_filter == "出品中のみ":
    filtered = [item for item in filtered if item.get("ステータス") == "出品中"]
elif status_filter == "売却済":
    filtered = [
        item for item in filtered
        if item.get("ステータス") not in ["出品中", "取下げ"]
    ]

# ============================================
# 🔢 並び替え
# ============================================
def parse_datetime(dt_str):
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except:
        return datetime.min

if sort_option == "新着順":
    filtered.sort(key=lambda x: parse_datetime(x.get("投稿日時", "")), reverse=True)
elif sort_option == "価格が安い順":
    filtered.sort(key=lambda x: x.get("価格", 0))
elif sort_option == "価格が高い順":
    filtered.sort(key=lambda x: x.get("価格", 0), reverse=True)

# ============================================
# 📄 ページネーション
# ============================================
ITEMS_PER_PAGE = 12
total_pages = (len(filtered) - 1) // ITEMS_PER_PAGE + 1

if "page" not in st.session_state:
    st.session_state["page"] = 1

def render_pagination_controls(position: str):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.session_state["page"] > 1:
            if st.button("← 前へ", key=f"{position}_prev_{st.session_state['page']}"):
                st.session_state["page"] -= 1
                st.rerun()
    with col3:
        if st.session_state["page"] < total_pages:
            if st.button("次へ →", key=f"{position}_next_{st.session_state['page']}"):
                st.session_state["page"] += 1
                st.rerun()
    with col2:
        st.markdown(f"ページ {st.session_state['page']} / {total_pages}")

render_pagination_controls("top")

# ============================================
# 🖼️ 商品表示（3列グリッド・画像ラベル付き）
# ============================================
start_idx = (st.session_state["page"] - 1) * ITEMS_PER_PAGE
end_idx = start_idx + ITEMS_PER_PAGE
page_items = filtered[start_idx:end_idx]

if page_items:
    for row_index in range(0, len(page_items), 3):
        row_items = page_items[row_index:row_index + 3]
        cols = st.columns(len(row_items))

        for col, item in zip(cols, row_items):
            with col:
                st.markdown('<div class="product-card">', unsafe_allow_html=True)

                image_url = item.get("画像URL", "")
                price = item.get("価格", "不明")
                condition = item.get("状態", "不明")
                product_id = item.get("商品ID", f"noid_{row_index}")

                # メイン画像＋ラベル
                if image_url:
                    st.markdown(
                        f"""
                        <div class="image-overlay">
                            <img src="{image_url}" />
                            <div class="label condition">{condition}</div>
                            <div class="label price">¥{price}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.write("画像なし")

                # 商品名・カテゴリ・ステータス
                st.markdown(f"**{item.get('商品名', '不明')}**")
                st.caption(f"カテゴリ: {item.get('カテゴリ', '不明')}")
                st.caption(f"ステータス: {item.get('ステータス', '不明')}")

                # 購入ボタン
                if item.get("ステータス") == "出品中":
                    if st.button("購入する", key=f"buy_{product_id}_{row_index}"):
                        st.session_state["selected_product"] = item
                        st.switch_page("pages/4_購入画面.py")
                        st.stop()

                st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("該当する商品が見つかりませんでした。")

render_pagination_controls("bottom")

# ============================================
# 📌 フッターメニュー
# ============================================
st.divider()
st.markdown("### 📌 メニュー")
with st.container():
    colA, colB, colC, colD = st.columns(4)
    colA.page_link("pages/2_商品検索.py", label="商品検索")
    colB.page_link("pages/3_出品画面.py", label="出品画面")
    colC.page_link("pages/7_マイページ（出品）.py", label="マイページ（出品）")
    colD.page_link("pages/6_マイページ（購入）.py", label="マイページ（購入）")