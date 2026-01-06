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
# 🔑 OAuth認証（キャッシュ）
# ============================================
@st.cache_resource
def get_gspread_client():
    creds_dict = json.loads(st.secrets["OAUTH_TOKEN"])
    creds = Credentials.from_authorized_user_info(creds_dict)
    return gspread.authorize(creds)

gc = get_gspread_client()

# ============================================
# 📄 商品データ取得（キャッシュ）
# ============================================
@st.cache_data(ttl=60)
def load_product_data():
    try:
        sheet = gc.open(st.secrets["PRODUCT_SHEET_NAME"]).sheet1
        raw_data = sheet.get_all_records()
        return [
            row for row in raw_data
            if row.get("商品名")
            and row.get("価格")
            and row.get("画像URL")   # メイン画像URLがあるものだけ
            and row.get("ステータス") != "取下げ"
        ]
    except Exception as e:
        st.error(f"商品データの取得に失敗しました: {e}")
        return []

data = load_product_data()
if not data:
    st.stop()

# ============================================
# 🎨 画像表示用 CSS（固定枠で高さを揃える）
# ============================================
st.markdown("""
<style>
.image-box {
    width: 200px;
    height: 200px;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 4px;
}
.image-box img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}
.thumb-box {
    width: 50px;
    height: 50px;
    overflow: hidden;
    border: 1px solid #ccc;
    margin-top: 2px;
}
.thumb-box img {
    width: 100%;
    height: 100%;
    object-fit: cover;
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
    filtered = [
        item for item in filtered
        if item.get("カテゴリ") == category_filter
    ]

if condition_filter != "すべて":
    filtered = [
        item for item in filtered
        if item.get("状態") == condition_filter
    ]

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
ITEMS_PER_PAGE = 6
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
# 🖼️ 商品表示（ギャラリー＋サムネイル切替）
# ============================================
start_idx = (st.session_state["page"] - 1) * ITEMS_PER_PAGE
end_idx = start_idx + ITEMS_PER_PAGE
page_items = filtered[start_idx:end_idx]

if page_items:
    num_cols = 2
    for row_index in range(0, len(page_items), num_cols):
        row_items = page_items[row_index:row_index + num_cols]
        cols = st.columns(len(row_items))

        for col, item in zip(cols, row_items):
            with col:
                with st.container():

                    product_id = item.get("商品ID", f"noid_{row_index}")

                    main_url = item.get("画像URL", "")
                    sub1_url = item.get("画像URLサブ1", "")
                    sub2_url = item.get("画像URLサブ2", "")

                    # 利用可能な画像一覧（空でないものだけ）
                    image_candidates = [url for url in [main_url, sub1_url, sub2_url] if url]

                    # 表示用の初期画像を決定
                    if f"thumb_{product_id}" not in st.session_state:
                        st.session_state[f"thumb_{product_id}"] = image_candidates[0] if image_candidates else ""

                    current_img = st.session_state.get(f"thumb_{product_id}", "")

                    # メイン画像（固定サイズ枠で高さを揃える）
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

                    # サムネイル切替（固定サイズの小枠）
                    thumb_urls = [main_url, sub1_url, sub2_url]
                    thumb_cols = st.columns(len(thumb_urls))

                    for idx, (thumb_col, url) in enumerate(zip(thumb_cols, thumb_urls)):
                        if not url:
                            continue
                        with thumb_col:
                            # 画像を表示する枠
                            st.markdown(
                                f"""
                                <div class="thumb-box">
                                    <img src="{url}" />
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            # クリックでメイン画像を切替
                            if st.button(f"{idx+1}", key=f"thumbbtn_{product_id}_{idx}"):
                                st.session_state[f"thumb_{product_id}"] = url

                    # 商品情報
                    st.markdown(f"**{item.get('商品名', '不明')}**")
                    st.markdown(f"**{item.get('価格', '不明')}円**")
                    st.caption(f"カテゴリ: {item.get('カテゴリ', '不明')}")
                    st.caption(f"状態: {item.get('状態', '不明')}")
                    st.caption(f"出品日時: {item.get('投稿日時', '不明')}")
                    st.caption(f"ステータス: {item.get('ステータス', '不明')}")

                    # 購入ボタン
                    if item.get("ステータス") == "出品中":
                        if st.button("購入する", key=f"buy_{product_id}_{row_index}"):
                            st.session_state["selected_product"] = item
                            st.switch_page("pages/4_購入画面.py")
                            st.stop()
else:
    st.warning("該当する商品が見つかりませんでした。")

render_pagination_controls("bottom")

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