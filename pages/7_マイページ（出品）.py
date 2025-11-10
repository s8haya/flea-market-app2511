import streamlit as st
import gspread
import json
import requests
from PIL import Image
import io
from google.oauth2.credentials import Credentials

st.set_page_config(page_title="マイページ（出品）", layout="centered")
st.title("マイページ（出品）")

# ログインチェック
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
        st.page_link("app.py")
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

# 商品データ取得
try:
    raw_data = sheet.get_all_records()
    user_id = str(st.session_state.get("id", "")).strip()
    listed_items = [
        row for row in raw_data
        if str(row.get("出品者ID", "")).strip() == user_id
    ]
except Exception as e:
    st.error(f"出品履歴の取得に失敗しました: {e}")
    st.stop()

# 商品表示
if listed_items:
    st.subheader("出品した商品一覧")
    for item in listed_items:
        with st.container(border=True):
            image_url = item.get("画像URL", "")
            if image_url:
                try:
                    response = requests.get(image_url)
                    img = Image.open(io.BytesIO(response.content))
                    st.image(img, width=160)
                except Exception:
                    st.caption(f"画像読み込み失敗: {image_url}")
            else:
                st.write("画像なし")

            st.markdown(f"**{item.get('商品名', '不明')}**")
            st.caption(f"{item.get('価格', '不明')}円 / {item.get('カテゴリ', '不明')}")
            st.caption(f"投稿日: {item.get('投稿日時', '不明')} / ステータス: {item.get('ステータス', '不明')}")

            status = item.get("ステータス", "")
            product_id = str(item.get("商品ID", "")).strip()

            # ✅ 出品中 → 取下げボタン表示
            if status == "出品中":
                if st.button("出品を取下げる", key=f"withdraw_{product_id}"):
                    try:
                        all_data = sheet.get_all_records()
                        row_index = next((i for i, row in enumerate(all_data) if str(row.get("商品ID", "")).strip() == product_id), None)
                        if row_index is not None:
                            sheet.update_cell(row_index + 2, 13, "取下げ")  # M列: ステータス
                            st.success("出品を取下げました。")
                            st.rerun()
                        else:
                            st.error("商品が見つかりませんでした。")
                    except Exception as e:
                        st.error(f"ステータス更新に失敗しました: {e}")

            # ✅ 購入状況に応じた情報表示
            if status in ["購入手続き中", "支払い確認中", "支払い確認済"]:
                purchaser = item.get("購入者名", "不明")
                purchase_time = item.get("購入日時", "不明")
                st.info(f"🛒 購入者: {purchaser} / 購入日時: {purchase_time}")

                if status == "購入手続き中":
                    st.warning("⚠️ 支払い処理が完了するまで、物品のお渡しはお待ちください。")
                else:
                    st.success("✅ 購入者と個別でやり取りのうえ、物品をお渡しください。")
else:
    st.info("出品履歴がありません。")

# フッターメニュー
st.divider()
st.markdown("### 📌 メニュー")
with st.container(horizontal=True):
    st.page_link("app.py", label="ログイン画面")
    st.page_link("pages/2_商品検索.py", label="商品検索")
    st.page_link("pages/3_出品画面.py", label="出品画面")
    st.page_link("pages/6_マイページ（購入）.py", label="マイページ（購入）")