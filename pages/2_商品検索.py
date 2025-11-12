# ✅ ページ切り替えUI（共通関数）
def render_pagination_controls():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.session_state["page"] > 1:
            if st.button("← 前へ", key=f"prev_{st.session_state['page']}"):
                st.session_state["page"] -= 1
                st.rerun()
    with col3:
        if st.session_state["page"] < total_pages:
            if st.button("次へ →", key=f"next_{st.session_state['page']}"):
                st.session_state["page"] += 1
                st.rerun()
    with col2:
        st.markdown(f"ページ {st.session_state['page']} / {total_pages}", unsafe_allow_html=True)

# ✅ 上部ページ切り替えUI
render_pagination_controls()

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
render_pagination_controls()

# ✅ フッターメニュー（共通4画面）
st.divider()
st.markdown("### 📌 メニュー")
with st.container(horizontal=True):
    st.page_link("pages/2_商品検索.py", label="商品検索")
    st.page_link("pages/3_出品画面.py", label="出品画面")
    st.page_link("pages/7_マイページ（出品）.py", label="マイページ（出品）")
    st.page_link("pages/6_マイページ（購入）.py", label="マイページ（購入）")