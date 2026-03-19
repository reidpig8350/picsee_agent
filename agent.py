import logging
import os

import requests
from google import genai
from google.genai import types

# (Local Modules)
import picsee_api

logging.getLogger('google_genai').setLevel(logging.ERROR)

class PicSeeAgent:
    def __init__(self):
        self.system_instruction = """
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
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY not set")

        self.client = genai.Client(api_key=self.google_api_key)
        self.model = "gemini-2.5-flash"

        self.tools = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="create_picsee_link",
                        description="使用 PicSee API 創建短連結，一次只能產生一個縮網址，執行後回傳deeplink url。使用者需要輸入page code, utm_source, utm_medium, utm_campaign。其中page code是必填, 而utm_source, utm_medium, utm_campaign則為選填。因為`utm_source`, `utm_medium`, `utm_campaign`是要放在URL的Query String，所以特殊符號要符合Query String的規範。例如不可以包含空白、`#`符號、`?`符號",
                        parameters=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            required=["page_code"],
                            properties={
                                "page_code": genai.types.Schema(type=genai.types.Type.STRING),
                                "utm_source": genai.types.Schema(type=genai.types.Type.STRING),
                                "utm_medium": genai.types.Schema(type=genai.types.Type.STRING),
                                "utm_campaign": genai.types.Schema(type=genai.types.Type.STRING),
                            },
                        ),
                    ),
                ]
            ),
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="short_link_analytics",
                        description="輸入短網址的URL或者短網址的ID，回傳指定短網址的總點擊數，並且一次只能回傳一個連結的數據。有限制條件：1. 無法依據時間區間回傳資料, 2. 如果使用者提供URL，網域必須是'cube.cathaybk.com.tw'或者'cube-app.tw'",
                        parameters=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            required=["link_url"],
                            properties={
                                "link_url": genai.types.Schema(type=genai.types.Type.STRING),
                            },
                        ),
                    ),
                ]
            ),
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="get_page_code_list",
                        description="取得所有可用的Page Code，回傳List of JSONs",
                        parameters=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                        ),
                    ),
                ]
            )
        ]

        self.generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=-1,
            ),
            tools=self.tools,
            system_instruction=[
                types.Part.from_text(text=self.system_instruction),
            ]
        )

    async def process_message(self, messages: list):
        contents_dialogs = [
            types.Content(
                role=msg.role,
                parts=[types.Part.from_text(text=msg.content)],
            )
            for msg in messages
        ]

        response = self.client.models.generate_content(model=self.model, contents=contents_dialogs, config=self.generate_content_config)

        # Check for function calls
        if response.candidates and response.candidates[0].content.parts and response.candidates[0].content.parts[0].function_call:
            function_call = response.candidates[0].content.parts[0].function_call
            tool_output = None
            tool_name = function_call.name

            try:
                if tool_name == "create_picsee_link":
                    tool_output = picsee_api.create_picsee_link(
                        page_code=function_call.args.get("page_code"),
                        utm_source=function_call.args.get("utm_source", "PicSee"),
                        utm_medium=function_call.args.get("utm_medium", "PicSee"),
                        utm_campaign=function_call.args.get("utm_campaign", "PicSee"),
                    )
                    if tool_output:
                        tool_output = {"url": tool_output}
                    else:
                        tool_output = {"error": "無法生成縮網址。"}

                elif tool_name == "short_link_analytics":
                    total_clicks = picsee_api.short_link_analytics(
                        link_url=function_call.args.get("link_url")
                    )
                    if total_clicks is not None:
                        tool_output = {"total_clicks": total_clicks}
                    else:
                        tool_output = {"error": "無法取得指定短網址的點擊數"}

                elif tool_name == "get_page_code_list":
                    page_code_list = picsee_api.get_page_code_list()
                    if page_code_list:
                        tool_output = {"page_code_list": page_code_list}
                    else:
                        tool_output = {"error": "無法取得Page Code清單"}

            except Exception as e: # Catch all exceptions here, specific HTTP or request exceptions can be handled inside picsee_api
                tool_output = {"error": f"Tool execution failed: {e}"}

            tool_message_content = types.Content(
                role='tool',
                parts=[
                    {"function_response": {
                        "name": tool_name,
                        "response": tool_output
                    }}
                ]
            )
            contents_dialogs.append(tool_message_content)
            response_after_processing_tool = self.client.models.generate_content(model=self.model, contents=contents_dialogs, config=self.generate_content_config)
            return response_after_processing_tool.text

        elif response.text:
            return response.text
        else:
            return "沒有回應。"
