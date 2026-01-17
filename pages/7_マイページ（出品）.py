import streamlit as st
import gspread
import json
from google.oauth2.credentials import Credentials
from datetime import datetime

st.set_page_config(page_title="マイページ（出品）", layout="centered")
st.title("マイページ（出品）")

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
# 📄 出品履歴取得
# ============================================
try:
    raw_data = sheet.get_all_records()
    user_id = str(st.session_state.get("id", "")).strip()
    my_items = [
        row for row in raw_data
        if str(row.get("出品者", "")).strip() == user_id
    ]
except Exception as e:
    st.error(f"出品履歴の取得に失敗しました: {e}")
    st.stop()

# ============================================
# 🎨 CSS（カード枠＋ギャラリー固定枠）
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

.withdraw-button {
    background-color: #888;
    color: white;
    padding: 8px 14px;
    border-radius: 6px;
    border: none;
    font-size: 14px;
    cursor: pointer;
}
.withdraw-button:hover {
    background-color: #666;
}

.restore-button {
    background-color: #2ECC71;
    color: white;
    padding: 8px 14px;
    border-radius: 6px;
    border: none;
    font-size: 14px;
    cursor: pointer;
}
.restore-button:hover {
    background-color: #27AE60;
}

.edit-button {
    background-color: #4A90E2;
    color: white;
    padding: 8px 14px;
    border-radius: 6px;
    border: none;
    font-size: 14px;
    cursor: pointer;
}
.edit-button:hover {
    background-color: #357ABD;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# 🖼️ 商品表示（ギャラリー＋カード枠）
# ============================================
if my_items:
    st.subheader("あなたの出品一覧")

    for item in my_items:
        product_id = item.get("商品ID", "noid")

        main_url = item.get("画像URL", "")
        sub1_url = item.get("画像URLサブ1", "")
        sub2_url = item.get("画像URLサブ2", "")

        image_candidates = [url for url in [main_url, sub1_url, sub2_url] if url]

        # 初期表示
        if f"mypage_sell_gallery_{product_id}" not in st.session_state:
            st.session_state[f"mypage_sell_gallery_{product_id}"] = image_candidates[0] if image_candidates else ""

        current_img = st.session_state[f"mypage_sell_gallery_{product_id}"]

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
                if st.button(f"{idx+1}", key=f"mypage_sell_thumb_{product_id}_{idx}"):
                    st.session_state[f"mypage_sell_gallery_{product_id}"] = url

        # 商品情報
        st.markdown(f"**{item.get('商品名', '不明')}**")
        st.markdown(f"**{item.get('価格', '不明')}円**")
        st.caption(f"カテゴリ: {item.get('カテゴリ', '不明')}")
        st.caption(f"状態: {item.get('状態', '不明')}")
        st.caption(f"投稿日時: {item.get('投稿日時', '不明')}")
        st.caption(f"ステータス: {item.get('ステータス', '不明')}")

        # ✅ 支払い済メッセージ表示
        if item.get("ステータス") == "支払い済":
            buyer_name = item.get("購入者名", "不明")
            buyer_dept = item.get("department", "不明")
            st.warning(
                f"""物品寄付いただきありがとうございました。  
当商品は **{buyer_dept}** の **{buyer_name}** さんが購入し、既に事務局に支払い済の状態です。  
メールがお二方に発信されておりますので、個人間で調整のうえ、物品を **{buyer_name}** さんにお渡しください。"""
            )

        # ボタン（修正 → 出品状態変更）
        colA, colB = st.columns(2)

        status = item.get("ステータス", "")

        # -------------------------
        # 修正ボタン（売買成立時は非表示）
        # -------------------------
        with colA:
            if status in ["購入手続き中", "支払い済"]:
                st.caption("※ この商品は修正できません")
            else:
                if st.button("修正", key=f"edit_{product_id}"):
                    st.session_state["edit_product"] = item
                    st.switch_page("pages/3_出品画面.py")
                    st.stop()

        # -------------------------
        # 出品状態変更ボタン
        # -------------------------
        with colB:

            # 出品中 → 取下げ
            if status == "出品中":
                if st.button("取下げ", key=f"withdraw_{product_id}"):
                    row_index = next((i for i, row in enumerate(raw_data)
                                      if row.get("商品ID") == product_id), None)
                    if row_index is not None:
                        sheet.update_cell(row_index + 2, 16, "取下げ")
                        st.success("商品を取下げました")
                        st.rerun()

            # 取下げ → 出品中に戻す
            elif status == "取下げ":
                if st.button("出品に戻す", key=f"restore_{product_id}"):
                    row_index = next((i for i, row in enumerate(raw_data)
                                      if row.get("商品ID") == product_id), None)
                    if row_index is not None:
                        sheet.update_cell(row_index + 2, 16, "出品中")
                        st.success("商品を再出品しました")
                        st.rerun()

            # 売買成立中（購入手続き中・支払い済）
            else:
                st.caption("※ この商品は現在操作できません")

        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("出品履歴がありません。")

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