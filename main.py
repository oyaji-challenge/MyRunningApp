import os
import json
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime

# 【追加】カレンダーの曜日の修正
st.set_page_config(page_title="RUNNING LOG", layout="centered")


#==============================================
#🔐 1. Googleスプレッドシートの接続設定(Render環境変数対応版)
#==============================================
# 接続に必要な権限の範囲を指定
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

@st.cache_resource
def init_connection():
    try:
        #➀Renderの環境変数から、秘密鍵の「文字列」を取得
        info_str = os.environ['GCP_SERVICE_ACCOUNT_KEY']

        #➁json部品を使って、文字列を「辞書形式(dict)」に変換
        info_dict = json.loads(info_str)

        #➂辞書データを使ってGoogleの認証部品を作成
        credentials = Credentials.from_service_account_info(info_dict, scopes=scopes)

        #➃gspreadに認証を渡して接続完了！
        return gspread.authorize(credentials)
    
    except KeyError:
        st.error("エラー： 環境変数 'GCP_SERVICE_ACCOUNT_KEY'が見つかりません。Renderの設定を確認してください。")
        return None
    except json.JSONDecodeError:
        st.error("エラー: 秘密鍵のJSON形式がただしくありません。Renderに貼り付けた中身を確認してください。")
        return None
    except Exception as e:
        st.error(f"Google Cloudとの接続に失敗しました: {e}")
        return None
    
#認証を実行して、スプレッドシート操作用のクライアント(gc)を作成
gc = init_connection()

# あなたのGoogleスプレッドシート名
SPREADSHEET_NAME = "myrunninglog"

#==================================================
# 📊 2. Streamlit 画面の作成(入力フォームと保存処理)
#==================================================
st.title("🏃‍♂️ RUNNING LOG (LAKE HACKER ver.)")
st.write("日々のランニング記録をスプレッドシートに安全に保存します。")

# 入力フォーム
with st.form("running_form", clear_on_submit=True):
    date = st.date_input("日付", datetime.date.today())
    distance = st.number_input("走行距離(km)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f")
    comment = st.text_input("メモ・今日のコンディション(フォーム、靴の摩耗など)")

    submit_button = st.form_submit_button(label="記録を保存する")

#保存ボタンが押された時の処理
if submit_button:
    if gc is not None:
        try:
            # スプレッドシートを開く
            sh = gc.open(SPREADSHEET_NAME)
            worksheet = sh.get_worksheet(0) # 1枚目のシート

            # 【自動化】 スプレッドシートの現在の行数を元に、次の行番号を計算
            next_row = len(worksheet.get_all_values()) + 1

            #【自動化】日付(A列)を基準に自動でさかのぼるための積算数式を生成
            formula_7d = f'=SUMIFS(B:B, A:A, ">="&(A{next_row}-6), A:A, "<="&A{next_row})'
            formula_30d = f'=SUMIFS(B:B, A:A, ">="&(A{next_row}-29), A:A, "<="&A{next_row})'

            #日付をスプレッドシートが100％自動認識できる文字形式に変換して送信
            date_str = date.strftime("%Y-%m-%d")
            row = [date_str, distance, formula_7d, formula_30d, comment]

            # 最新のgspread仕様に合わせた、リストのリスト形式で一括流し込み
            worksheet.append_rows([row], value_input_option="USER_ENTERED")

            # 無事に通過すれば、100％確実に保存成功です！
            st.success(f"🎉 記録を保存しました！ ({date} : {distance}km)")

        except Exception as e:
            #正常通信なのにResponse[200]をエラーと着検知してしまった場合の保険
            error_msg = str(e)
            if "200" in error_msg or "Response [200]" in error_msg:
                st.success(f"🎉 記録を保存しました！ ({date} : {distance}km)")
            else:
                st.error(f"スプレッドシートへの書き込みに失敗しました: {e}")
    else:
        st.error("認証が通っていないため、保存できません。Renderの環境変数設定を確認してください。")
