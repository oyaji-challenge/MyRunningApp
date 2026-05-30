import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime

#============================================
#1. Googleスプレッドシートの接続設定
#============================================
#接続に必要な権限の範囲を指定
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

#安全に配置された「secret.json」を読み込んで認証
@st.cache_resource
def init_connection():
    try:
        credentials = Credentials.from_service_account_file('secret.json', scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Google Cloudとの接続に失敗しました。鍵ファイル(secret.json)を確認してください: {e}")
        return None
    
gc = init_connenction()

#あなたのGoogleスプレッドシート名(必要に応じて書き換えてください)
#※このIDや名前は一般に公開されてもセキュリティ上問題ありません
SPREADSHEET_NAME = "myrunninglog"

#=============================================
#2.Streamlit 画面の作成
#=============================================
st.title("🏃‍♂️ RUNNING LOG (LAKE HACKER ver.)")
st.write("日々のランニング記録をスプレッドシートに安全に保存します。")

#入力フォーム
with st.form("running_form", clear_on_submit=True):
    date = st.date_input("日付", datetime.date.today())
    distance = st.number_input("走行距離 (km)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f")
    duration_min =st.number_input("時間 (分)", min_value=0, max_value=600, step=1)
    comment = sst.text_input("メモ・今日のコンディション (フォーム、靴の摩耗など)")

    submit_button = st.form_submit_button(label="記録を保存する")

#保存ボタンが押された時の処理
if submit_button:
    if gc is not None:
        try:
            #スプレッドシートを開く
            sh = gc.open(SPREADSHEET_NAME)
            worksheet = sh.get_worksheet(0) #1枚目のシート

            #保存するデータの並び
            row = [str(date), distance, duration_min, comment]

            #シートの最下行にデータを追加
            worksheet.append_row(row)

            st.success(f"🎉 記録を保存しました！ ({date} : {distance}km)")
        except Exception as e:
            st.error(f"スプレッドシートへの書き込みに失敗しました: {e}")
    else:
        st.error("認証が通っていないため、保存できません。")