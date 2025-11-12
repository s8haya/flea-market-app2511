# ✅ ページネーション設定
ITEMS_PER_PAGE = 6
total_pages = (len(filtered) - 1) // ITEMS_PER_PAGE + 1
if "page" not in st.session_state:
    st.session_state["page"] = 1

# ✅ ページ切り替えUI（共通関数）※呼び出しより前に定義
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
        st.markdown(f"ページ {st.session_state['page']} / {total_pages}", unsafe_allow_html=True)

# ✅ 上部ページ切り替えUI
render_pagination_controls("top")

# ✅ 表示対象アイテム抽出
start_idx = (st.session_state["page"] - 1) * ITEMS_PER_PAGE
end_idx = start_idx + ITEMS_PER_PAGE
page_items = filtered[start_idx:end_idx]

# ✅ 商品表示（カード風グリッド）
if page_items:
    num_cols = 2
    for i in range(0, len(page_items), num_cols):
        row_items = page_items[i:i+num_cols]
        cols = st.columns(len(row_items))
        for col, item in zip(cols, row_items):
            with col:
                with st.container():
                    image_url = item.get("画像URL", "")
                    if image_url:
                        try:
                            response = requests.get(image_url, stream=True, timeout=3)
                            img = Image.open(io.BytesIO(response.content))
                            img = crop_center_square(img)
                            img = img.resize((160, 160))
                            st.image(img)
                        except Exception:
                            st.warning("画像の読み込みに失敗しました。")
                            st.caption(f"画像URL: {image_url}")
                    else:
                        st.write("画像なし")

                    st.markdown(f"**{item.get('商品名', '不明')}**")
                    st.caption(f"{item.get('価格', '不明')}円 / {item.get('カテゴリ', '不明')}")
                    st.caption(f"{item.get('出品者名', '不明')} / {item.get('投稿日時', '不明')}")
                    st.caption(f"ステータス: {item.get('ステータス', '不明')}")

                    if item.get("ステータス") == "出品中":
                        product_id = item.get("商品ID")
                        if product_id:
                            if st.button("購入する", key=f"buy_{product_id}"):
                                st.session_state["selected_product"] = item
                                st.switch_page("pages/4_購入画面.py")
                                st.stop()
else:
    st.warning("該当する商品が見つかりませんでした。")

# ✅ 下部ページ切り替えUI（複製）
render_pagination_controls("bottom")