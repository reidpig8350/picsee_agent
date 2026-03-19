import requests
import os
import json
from dotenv import load_dotenv

# 加載 .env 檔案（如果存在的話）
load_dotenv()

# 取得環境變數
# 不論是在地端的 .env 還是 Cloud Run 的環境變數設定，都用這行讀取
picsee_access_token = os.getenv("PICSEE_ACCESS_TOKEN")

if not picsee_access_token:
    print("警告：找不到 PICSEE_ACCESS_TOKEN 環境變數")

system_instruction = """
    **Agent System Instruction:**

    **目標：** 使用 PicSee API 創建短網址，引導客戶的手機打開CUBE App。

    **Page Code 的定義：**

    *   Page Code 是國泰世華 APP 中每個頁面獨一無二的代號，用於唯一識別 APP 中的特定頁面，透過Page Code可以引導CUBE App打開指定畫面。
    *   它類似於網頁的網址。APP 開發團隊對外將此頁面代號稱為 "Page Code"。
    *   **重要：** Page Code 與 APP 頁面的連結需要額外開發。如果使用者的行銷需求無法從現有的 "Page Code 清單" 中滿足，則必須向 APP 開發團隊提出新的 Page Code 需求。可透過信件向數位銀行科技部的施景輔聯繫，

    **使用者輸入：**

    *   **必填：** `page code`
    *   **選填：** `utm_source`, `utm_medium`, `utm_campaign`

    **`page code` 規則：**

    1.  **格式驗證：**
        *   必須符合 兩個大寫英文字開頭 + 四個數字，例如AC1014。
        *   若格式不符，告知使用者正確格式，並提供以下訊息： "page code 格式錯誤，請確認格式為兩個英文大寫字母加上四個數字 (例如：AC1014)。"
        *   告知使用者，若需要協助，可以聯繫數位銀行發展部的朱修弘 (分機8000#3109) 或范育豪 (分機8000#6190) 索取。
    2.  **有效性驗證：**
        *   使用者提供的 `page code` 必須存在於以下 Page Code 清單中。
        *   如果使用者使用中文描述想要使用的連結，就透過get_page_code_list這個function取得Page Code List，讓使用者確認其想使用的連結所對應的 `page code`。
        *   如果使用者想直接索取 Page Code 清單，就透過get_page_code_list這個function取得Page Code List。
    3.  **Page Code 清單：**

    **UTM 參數規則：**

    1.  **選填性質：** `utm_source`, `utm_medium`, `utm_campaign` 皆為選填。
    2.  **未填寫 UTM 參數的處理：**
        *   若使用者只輸入了有效的 `page code`，但未提供任何 UTM 參數，告知使用者： "您只提供了 Page Code，未提供 UTM 參數。這代表您將無法在 Google Analytics 中追蹤此連結的成效。請問您是否確定要使用預設的 UTM 參數？"
        *   如果使用者確認不需追蹤，則使用預設的 UTM 參數產生短網址。 (預設的UTM是utm_source=PicSee, utm_medium=PicSee, utm_campaign=PicSee)
    3.  **UTM格式：** 因為`utm_source`, `utm_medium`, `utm_campaign`是要放在URL的Query String，所以特殊符號要符合Query String的規範。例如不可以包含空白、`#`符號、`?`符號

    **其他選項：**

    *   **批次產生：** 如果使用者想要一次產多個縮網址，告知他們可以填寫 M365 Excel 表單，數位銀行發展部將會在雙周的週四 16:00 批次產生短網址。
        *   提供表單連結：[Deeplink申請表](https://cube-app.tw/83vugw)

    **API 呼叫：**

    1.  將 `page code` 放入 PicSee API 的 query string 參數 `content` 中。
    2.  將 `utm_source`, `utm_medium`, `utm_campaign` 放入 PicSee API 的對應參數中。

    **總結流程：**

    1.  取得使用者輸入的 `page code`。
    2.  驗證 `page code` 格式是否正確。不正確則告知使用者並停止。
    3.  驗證 `page code` 是否存在於清單中。不存在則告知使用者並停止。
    4.  檢查是否缺少 UTM 參數。
        *   若缺少，告知使用者缺少 UTM 參數的風險。
        *   若使用者確認，則使用預設 UTM 參數。(預設的UTM是utm_source=PicSee, utm_medium=PicSee, utm_campaign=PicSee)
    5.  呼叫 PicSee API 產生短網址。
    6.  回覆使用者產生的短網址。
    7.  提醒使用者以下注意事項：
        使用前務必請用外部裝置測試，目前行內電腦無法開啟網域為cube.cathaybk.com.tw的縮網址。
        測試方式建議如下：
            1. 把連結複製到 Cteam 的對話框
            2. 從手機，把連結複製到其他的 App 例如 LINE 的對話框
            3. 點擊該連結，連結引導手機自動打開 CUBE App 指定頁面
    8.  詢問使用者是否要接著產下一個短網址。

"""
def get_page_code_list():
    page_code_list = [
        {"page_code": "AC1014", "app_screen_name": "帳務總覽"},
        {"page_code": "AC2002", "app_screen_name": "外幣帳務總覽"},
        {"page_code": "AC2007", "app_screen_name": "匯率走勢內頁-美金"},
        {"page_code": "AC2007", "app_screen_name": "外幣買賣_美金"},
        {"page_code": "AC2009", "app_screen_name": "外幣買賣頁"},
        {"page_code": "AC2010", "app_screen_name": "信用卡首頁"},
        {"page_code": "AC2011", "app_screen_name": "信用卡帳單資訊"},
        {"page_code": "AC2012", "app_screen_name": "信用卡未出帳消費明細"},
        {"page_code": "AC2012", "app_screen_name": "信用卡未出帳明細"},
        {"page_code": "AC2013", "app_screen_name": "繳費繳稅 → 繳費繳稅"},
        {"page_code": "AC2014", "app_screen_name": "信用卡即時消費紀錄"},
        {"page_code": "AC2015", "app_screen_name": "CUBE方案總覽"},
        {"page_code": "AC2017", "app_screen_name": "新轉帳"},
        {"page_code": "AC2017", "app_screen_name": "台幣轉帳頁"},
        {"page_code": "AC2020", "app_screen_name": "任務牆"},
        {"page_code": "AC2021", "app_screen_name": "信用卡帳單→轉帳繳卡款"},
        {"page_code": "AC2022", "app_screen_name": "手機提款交易頁"},
        {"page_code": "AC2025", "app_screen_name": "刷到保"},
        {"page_code": "AC3006", "app_screen_name": "信用卡-自動扣繳設定"},
        {"page_code": "AC3017", "app_screen_name": "加碼活動(XYZ)(待領取)"},
        {"page_code": "AC3010", "app_screen_name": "信用卡臨時調整額度"},
        {"page_code": "AC3012", "app_screen_name": "分期專區"},
        {"page_code": "AC4001", "app_screen_name": "視訊客服－設定約轉頁"},
        {"page_code": "CS2001", "app_screen_name": "投資總覽－證券"},
        {"page_code": "CS2002", "app_screen_name": "證券首頁_美股"},
        {"page_code": "CS3001", "app_screen_name": "證券內頁右下角”更多台股”"},
        {"page_code": "CS3002", "app_screen_name": "證券內頁右下角”更多美股”"},
        {"page_code": "EB2001", "app_screen_name": "開戶3-1戶"},
        {"page_code": "FC3001", "app_screen_name": "更多匯率"},
        {"page_code": "FC3002", "app_screen_name": "外幣開戶(PROD)"},
        {"page_code": "FD2019", "app_screen_name": "投資總覽－基金"},
        {"page_code": "FD3007", "app_screen_name": "投資_基金_KYC"},
        {"page_code": "FD3008", "app_screen_name": "基金申購"},
        {"page_code": "FD3010", "app_screen_name": "精選基金"},
        {"page_code": "FD3011", "app_screen_name": "簽署信託"},
        {"page_code": "FD4011", "app_screen_name": "瀏覽排行"},
        {"page_code": "FD4012", "app_screen_name": "個人化推薦"},
        {"page_code": "FD4013", "app_screen_name": "話題基金"},
        {"page_code": "IS2001", "app_screen_name": "利即保"},
        {"page_code": "IS2002", "app_screen_name": "保險專區"},
        {"page_code": "LN2001", "app_screen_name": "信貸首頁"},
        {"page_code": "LN3011", "app_screen_name": "保單貸款(PROD)"},
        {"page_code": "LN3012", "app_screen_name": "我的彈力貸(PROD)"},
        {"page_code": "ME2017", "app_screen_name": "疫苗險"},
        {"page_code": "ME2018", "app_screen_name": "汽車險"},
        {"page_code": "ME2019", "app_screen_name": "機車險"},
        {"page_code": "ME2089", "app_screen_name": "裝置綁定"},
        {"page_code": "ME3001", "app_screen_name": "更多 → 交易認證碼"},
        {"page_code": "ME3004", "app_screen_name": "更多 → 設定"},
        {"page_code": "ME3005", "app_screen_name": "更多 → 專屬優惠"},
        {"page_code": "ME3007", "app_screen_name": "個人資料頁"},
        {"page_code": "ME4001", "app_screen_name": "更多→設定→登入方式設定"},
        {"page_code": "ME4003", "app_screen_name": "更多→設定→推播設定"},
        {"page_code": "ME4004", "app_screen_name": "手機號碼連結帳號"},
        {"page_code": "ME4005", "app_screen_name": "本人國泰帳戶互轉"},
        {"page_code": "ME4010", "app_screen_name": "手機提款設定頁"},
        {"page_code": "ME4011", "app_screen_name": "到價通知設定頁(匯率到價)"},
        {"page_code": "ME4012", "app_screen_name": "更多→帳戶→匯出台外幣電子存摺"},
        {"page_code": "ME4013", "app_screen_name": "修改個人資料 (手機號碼設定)"},
        {"page_code": "ME4014", "app_screen_name": "更多_人臉辨識註冊"},
        {"page_code": "RB0000", "app_screen_name": "Robo - 智能投資總覽"},
        {"page_code": "RB1001", "app_screen_name": "RB1001 投資 - 智能投資 - Product Inf"},
        {"page_code": "RB1005", "app_screen_name": "智能幫你選"},
        {"page_code": "RB2002", "app_screen_name": "收費方式"},
        {"page_code": "RB2003", "app_screen_name": "GBI頁"},
        {"page_code": "RB2004", "app_screen_name": "TBI頁_永續"},
        {"page_code": "RB2005", "app_screen_name": "TBI頁_全球"},
        {"page_code": "RB2006", "app_screen_name": "TBI頁_亞洲"},
        {"page_code": "RB2007", "app_screen_name": "TBI頁_趨勢"},
        {"page_code": "RB2008", "app_screen_name": "TBI頁_月領"},
        {"page_code": "RB2009", "app_screen_name": "TBI頁_股債"}
    ]
    return page_code_list

def short_link_analytics(link_url):

    encode_id = link_url.strip('/').split('/')[-1]
    url = f'https://api.pics.ee/v1/links/{encode_id}/overview'

    params = {'access_token': picsee_access_token, 'encodeId': encode_id}
    headers = {'Content-Type': 'application/json'}
    response = requests.get(url, headers=headers, params=params)
    return response.json()['data']['dailyClicks'][0]['totalClicks']

def create_picsee_link(page_code, utm_source='PicSee', utm_medium='PicSee', utm_campaign='PicSee'):
    """
    使用 Pics.ee API 創建短連結。使用者需要輸入page code, utm_source, utm_medium, utm_campaign
    其中page code必須要填在query string的content, 而utm_source, utm_medium, utm_campaign則為選填。
    如果page code格式不符合要求，就必須告訴使用者格式為兩個英文加四個數字。並且要向系統負責人索取正確的page code
    """
    url = 'https://api.pics.ee/v1/links'
    params = {'access_token': picsee_access_token}
    headers = {'Content-Type': 'application/json'}
    long_url = f"https://www.cathaybk.com.tw/cathaybk/promo/event/ebanking/product/appdownload/index.html?action=page&content={page_code}&cubsource={utm_source}&cubmedium={utm_medium}&cubcampaign={utm_campaign}"
    deep_link = f"mymobibank://?action=page&content={page_code}&utm_source={utm_source}&utm_medium={utm_medium}&utm_campaign={utm_campaign}"
    data = {
        "url": long_url,
        "domain": "cube-app.tw",
        "targets": [
            {"target": "ios", "url": deep_link},
            {"target": "android", "url": deep_link}
        ]
    }

    try:
        response = requests.post(url, headers=headers, params=params, data=json.dumps(data))
        response.raise_for_status()
        response_json = response.json()
        if 'data' in response_json and 'picseeUrl' in response_json['data']:
            return response_json['data']['picseeUrl']
        else:
            print(f"警告：API 回應中缺少 'data' 或 'picseeUrl'。代碼前綴：{page_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"為代碼前綴 '{page_code}' 創建短連結時發生錯誤：{e}")
        return None
    except json.JSONDecodeError:
        print(f"警告：無法解析 API 回應為 JSON。代碼前綴：{page_code}")
        return None

if __name__ == '__main__':
    
    print(create_picsee_link('AC1014'))