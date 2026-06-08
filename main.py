import os
import json
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime

#============================================
#🔐 1. Googleスプレッドシートの接続設定(Render環境変数対応版)
#============================================
#接続に必要な権限の範囲を指定
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

@st.cache_resource
def init_connection():
    try:
        #➀ Renderの環境変数から、秘密鍵の「文字列」を取得
        info_str = os.environ['GCP_SERVICE_ACCOUNT_KEY']

        #➁ 【重要】json部品を使って、文字列を「辞書形式(dict)」に変換
        info_dict = json.loads(info_str)

        #➂ 辞書データを使ってGoogleの認証部品を作成(scopesも一緒に渡します)
        credentials = Credentials.from_service_account_info(info_dict,scopes=scopes)

        #➃ gspreadに認証を渡して接続完了！
        return gspread.authorize(credentials)
    
    except KeyError:
        st.error("エラー: 環境変数 'GCP_SERVICE_ACCOUNT_KEY'が見つかりません。Renderの設定を確認してください。")
        return None
    except json.JSONDecodeError:
        st.error("エラー: 秘密鍵のJSON形式が正しくありません。Renderに貼り付けた中身を確認してください。")
        return None
    except Exception as e:
        st.error(f"Google Cloudとの接続に失敗しました: {e}")
        return None
    
#認証を実行して、スプレッドシート操作用のクライアント(gc)を作成
gc = init_connection()

#あなたのGoogleスプレッドシート名
SPREADSHEET_NAME = "myrunninglog"

#===============================================
# 📊 2. Streamlit 画面の作成 (入力フォームと保存処理)
#===============================================
st.title("🏃‍♂️ RUNNING LOG (LAKE HACKER ver.)")
st.write("日々のランニング記録をスプレッドシートに安全に保存します。")

# 入力フォーム
with st.form("running_form", clear_on_submit=True):
    date = st.date_input("日付", datetime.date.today())
    distance = st.number_input("走行距離 (km)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f")
    duration_min = st.number_input("時間 (分)", min_value=0, max_value=600, step=1)

    # 💡 さりげなく「sst.text_input」になっていたスペルミスを「st.text_input」に修正しました！
    comment = st.text_input("メモ・今日のコンディション(フォーム、靴の摩耗など)")

    submit_button = st.form_submit_button(label="記録を保存する")

#保存ボタンが押された時の処理
if submit_button:
    if gc is not None:
        try:
            #スプレッドシートを開く
            sh = gc.open(SPREADSHEET_NAME)
            worksheet = sh.get_worksheet(0) # 1枚目のシート

            # 保存するデータの並び
            row = [str(date), distance, duration_min, comment]

            # シートの最下行にデータを追加
            worksheet.append_row(row, value_input_option="USER_ENTERED")

            st.success(f"🎉 記録を保存しました！ ({date} : {distance}km)")
        except Exception as e:
            st.error(f"スプレッドシートへの書き込みに失敗しました: {e}")
    else:
        st.error("認証が通っていないため、保存できません。Renderの環境変数設定を確認して下さい。")   