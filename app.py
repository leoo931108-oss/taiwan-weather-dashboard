import requests
import streamlit as st
import pandas as pd
import json
import os
import urllib3

# 關閉 SSL 警告（因為 verify=False）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 讀取 API Key（從 Streamlit Cloud Secrets）
API_KEY = os.environ.get("CWA_API_KEY")

DATASTORE_ID = "F-C0032-001"

# 全台 22 縣市
LOCATIONS = [
    "臺北市","新北市","桃園市","臺中市","臺南市","高雄市",
    "基隆市","新竹市","嘉義市",
    "新竹縣","苗栗縣","彰化縣","南投縣","雲林縣",
    "嘉義縣","屏東縣","宜蘭縣","花蓮縣","臺東縣",
    "澎湖縣","金門縣","連江縣"
]


def fetch_city_weather(city):
    """抓單一縣市的36小時預報資料"""

    url = (
        f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/{DATASTORE_ID}"
        f"?Authorization={API_KEY}&locationName={city}"
    )

    # 🔥 修正 Streamlit Cloud 的 SSL 錯誤
    res = requests.get(url, verify=False)
    data = res.json()

    if data.get("success") != "true":
        return None

    location = data["records"]["location"][0]
    elements = location["weatherElement"]

    # 低溫 / 高溫資料
    min_temp_times = next((e["time"] for e in elements if e["elementName"] == "MinT"), [])
    max_temp_times = next((e["time"] for e in elements if e["elementName"] == "MaxT"), [])

    # 36 小時溫度資料
    chart_data = []
    for min_t, max_t in zip(min_temp_times, max_temp_times):
        time_point = pd.to_datetime(min_t["startTime"]).strftime("%m-%d %H:%M")
        chart_data.append({
            "時間": time_point,
            "最低溫": int(min_t["parameter"]["parameterName"]),
            "最高溫": int(max_t["parameter"]["parameterName"])
        })

    df_chart = pd.DataFrame(chart_data).set_index("時間")

    # 天氣要素表格
    table_data = [
        {
            "天氣要素": e["elementName"],
            "預報值": e["time"][0]["parameter"]["parameterName"]
        }
        for e in elements
    ]
    df_table = pd.DataFrame(table_data)

    return df_chart, df_table



def main():
    st.set_page_config(layout="wide")
    st.title("🌤️ 台灣氣象資料 Dashboard")
    st.markdown("中央氣象署開放資料（F-C0032-001）")
    st.markdown("---")

    # 檢查 API Key 是否存在
    if not API_KEY:
        st.error("❌ 找不到 API Key！請到 Streamlit Cloud 的 Secrets 設定 CWA_API_KEY。")
        return

    # 縣市選單
    selected_city = st.selectbox("選擇縣市", LOCATIONS)

    result = fetch_city_weather(selected_city)

    if result is None:
        st.error("❌ 無法取得資料，請確認 API Key 或縣市名稱是否正確。")
        return

    df_chart, df_table = result

    # 📈 繪製 36 小時溫度折線圖
    st.subheader(f"📈 {selected_city} - 未來 36 小時溫度趨勢")
    st.line_chart(df_chart)
    st.markdown("---")

    # 📋 詳細資料表格
    st.subheader(f"📋 {selected_city} - 天氣詳細資訊")
    st.table(df_table)



if __name__ == "__main__":
    main()
