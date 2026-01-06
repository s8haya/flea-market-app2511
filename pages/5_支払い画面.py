import streamlit as st
import gspread
import json
from PIL import Image
from datetime import datetime
from google.oauth2.credentials import Credentials
import pytz
import time
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
import pandas as pd

st.set_page_config(page_title="支払い画面", layout="centered")
st.title("支払い画面")

# ---------------------------------------------------------
# ログインチェック
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# 商品情報取得
# ---------------------------------------------------------
product = st.session_state.get("selected_product")
if not product:
    st.warning("商品情報が見つかりませんでした。")
    st.switch_page("pages/2_商品検索.py")
    st.stop()

# ---------------------------------------------------------
# OAuth 認証
# ---------------------------------------------------------
try:
    creds_dict = json.loads(st.secrets["OAUTH_TOKEN"])
    creds = Credentials.from_authorized_user_info(creds_dict)
    gc = gspread.authorize(creds)
    sheet = gc.open(st.secrets["PRODUCT_SHEET_NAME"]).sheet1
    user_sheet = gc.open(st.secrets["USER_SHEET_NAME"]).sheet1
except Exception as e:
    st.error(f"Google Sheetsの認証に失敗しました: {e}")
    st.stop()

# ---------------------------------------------------------
# メール送信関数（CC対応）
# ---------------------------------------------------------
def send_mail(to_list, subject, body, cc_list=None):
    from_addr = st.secrets["EMAIL_ADDRESS"]
    password = st.secrets["EMAIL_PASSWORD"]

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg["Date"] = formatdate()

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(from_addr, password)
        server.sendmail(from_addr, to_list + (cc_list or []), msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"メール送信に失敗しました: {e}")
        return False

# ---------------------------------------------------------
# 商品情報表示（出品者情報は表示しない）
# ---------------------------------------------------------
st.subheader("購入商品情報")
st.markdown(f"**{product.get('商品名', '不明')}**")
st.write(f"価格: {product.get('価格', '不明')}円")
st.caption("※出品者情報は、下記支払い対応後に開示されます。")

st.divider()
st.subheader("以下のQRコードからお支払いください")

# QRコード表示
try:
    qr_image = Image.open("QRsuzuki.png")
    st.image(qr_image, width=240)
except Exception:
    st.error("QRコード画像の読み込みに失敗しました。QRsuzuki.png が正しく配置されているか確認してください。")
    st.stop()

# ---------------------------------------------------------
# あとで支払う
# ---------------------------------------------------------
if st.button("paypayであとで支払う"):
    st.info("マイページから後ほどお支払いください。")
    st.switch_page("pages/6_マイページ（購入）.py")
    st.stop()

# ---------------------------------------------------------
# 現金払い案内
# ---------------------------------------------------------
st.caption("現金払いをご希望の方は、下記自動メール配信ボタンを押下し、「ITデジ戦 鈴木（啓）・工藤・木屋」までご連絡ください。")

# ---------------------------------------------------------
# 現金払い依頼メール（確認ステップ付き）
# ---------------------------------------------------------

if "confirm_cash_mail" not in st.session_state:
    st.session_state["confirm_cash_mail"] = False

if not st.session_state["confirm_cash_mail"]:
    if st.button("事務局宛の現金払い依頼メール（自動配信）"):
        st.session_state["confirm_cash_mail"] = True
        st.rerun()
else:
    st.warning("現金払い依頼メールを事務局に送信しますか？")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("送信する"):
            try:
                user_df = pd.DataFrame(user_sheet.get_all_records(), dtype=str)

                # ✅ 修正：ログイン中ユーザーのIDを使用
                buyer_id = str(st.session_state.get("id", "")).strip()
                if not buyer_id:
                    st.error("ログインユーザーのIDが取得できませんでした。再ログインしてください。")
                else:
                    hit = user_df.query("id == @buyer_id")
                    if hit.empty:
                        st.error(f"ユーザーID {buyer_id} に該当するユーザー情報が見つかりませんでした。")
                    else:
                        buyer_email = hit["mail"].values[0]
                        buyer_dept = hit["department"].values[0]
                        buyer_name = st.session_state["username"]

                        product_name = product.get("商品名", "")
                        price = product.get("価格", "")
                        category = product.get("カテゴリ", "")
                        purchase_time = datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S")

                        subject = f"【現金払い依頼】{buyer_dept} {buyer_name}さんが「{product_name}」の現金払いを希望しています"

                        body = f"""
事務局各位

以下の商品について、購入者より現金払いの希望がありました。

【商品名】{product_name}
【価格】{price}円
【カテゴリ】{category}
【購入者】{buyer_dept} {buyer_name}
【購入日時】{purchase_time}

現金払いの対応をお願いいたします。
このメールはシステムからの自動配信です。
"""

                        send_mail(
                            [buyer_email],
                            subject,
                            body,
                            cc_list=[
                                "ke7-suzuki@meijiyasuda.co.jp",
                                "ji-kudou@meijiyasuda.co.jp",
                                "ha-kiya@meijiyasuda.co.jp"
                            ]
                        )

                        st.success("事務局宛に現金払い依頼メールを送信しました。対応をお待ちください。")

            except Exception as e:
                st.error(f"現金払い依頼メールの送信に失敗しました: {e}")

            st.session_state["confirm_cash_mail"] = False

    with col2:
        if st.button("キャンセル"):
            st.session_state["confirm_cash_mail"] = False
            st.info("送信をキャンセルしました。")

st.divider()
st.subheader("支払い後の操作")

# ---------------------------------------------------------
# 支払い済処理
# ---------------------------------------------------------
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

        # ステータス更新
        sheet.update_cell(row_index + 2, 16, "支払い確認中")
        time.sleep(1)

        # メール送信処理
        user_df = pd.DataFrame(user_sheet.get_all_records(), dtype=str)
        seller_id = str(product.get("出品者", "")).strip()
        buyer_id = str(product.get("購入者", "")).strip()

        seller_email = user_df.query("id == @seller_id")["mail"].values[0]
        buyer_email = user_df.query("id == @buyer_id")["mail"].values[0]
        seller_dept = user_df.query("id == @seller_id")["department"].values[0]
        buyer_dept = user_df.query("id == @buyer_id")["department"].values[0]

        seller_name = product.get("出品者名", "")
        buyer_name = st.session_state["username"]
        product_name = product.get("商品名", "")
        price = product.get("価格", "")
        category = product.get("カテゴリ", "")
        purchase_time = all_data[row_index].get("購入日時", "")

        subject = f"システム自動配信：{seller_name}さんの出品「{product_name}」を{buyer_name}さんが購入しました"

        body = f"""
{seller_dept} {seller_name}さん、{buyer_dept} {buyer_name}さん

このメールはシステムからの自動配信です。

以下の商品について、購入者による支払いが完了しました。

【商品名】{product_name}
【価格】{price}円
【カテゴリ】{category}
【出品者】{seller_dept} {seller_name}
【購入者】{buyer_dept} {buyer_name}
【購入日時】{purchase_time}

出品者の方は、購入者へ商品をお渡しください。
購入者の方は、出品者から商品を受領してください。

今後ともよろしくお願いいたします。
"""

        send_mail(
            [seller_email, buyer_email],
            subject,
            body,
            cc_list=[
                "ke7-suzuki@meijiyasuda.co.jp",
                "ji-kudou@meijiyasuda.co.jp",
                "ha-kiya@meijiyasuda.co.jp"
            ]
        )

        st.success(
            f"購入ありがとうございました。システム自動メールを出品者・購入者に配信しました。\n"
            f"出品者：{seller_dept} {seller_name}さんと個人間でやり取り頂いたうえで、商品譲渡の対応をお願いします。"
        )

    except Exception as e:
        st.error(f"支払い処理中にエラーが発生しました: {e}")

# ---------------------------------------------------------
# フッターメニュー
# ---------------------------------------------------------
st.divider()
st.markdown("### 📌 メニュー")
with st.container(horizontal=True):
    st.page_link("pages/2_商品検索.py", label="商品検索")
    st.page_link("pages/3_出品画面.py", label="出品画面")
    st.page_link("pages/7_マイページ（出品）.py", label="マイページ（出品）")
    st.page_link("pages/6_マイページ（購入）.py", label="マイページ（購入）")