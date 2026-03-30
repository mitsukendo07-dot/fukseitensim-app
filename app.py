import streamlit as st
import requests
from bs4 import BeautifulSoup
import concurrent.futures

# アプリの基本設定
st.set_page_config(page_title="福岡 晴天率シミュレーター", page_icon="💍")

# タイトルと説明文
st.title("💍 福岡ウエディング\n晴天率シミュレーター")
st.write("過去30年分の気象庁データから、雨が降らない確率を計算します。")

# 月と日を選ぶ入力欄を横並びに配置
col1, col2 = st.columns(2)
with col1:
    month = st.selectbox("月を選択", list(range(1, 13)), index=9) # 初期値は10月
with col2:
    day = st.selectbox("日を選択", list(range(1, 32)), index=9) # 初期値は10日

# 気象庁のデータを取得する関数
def fetch_year_data(year, month, day):
    url = "https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php"
    params = {"prec_no": "82", "block_no": "47807", "year": str(year), "month": str(month), "day": "", "view": "p1"}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all(['th', 'td'])
            # 一番左の列が指定した日と一致するか
            if cols and cols[0].text.strip() == str(day):
                if len(cols) >= 5:
                    weather = cols[-2].text.strip()
                    if weather and weather != "×" and weather != "//":
                        # 晴れ・快晴を含み、雨・雪を含まない
                        is_sunny = ("晴" in weather or "快晴" in weather) and "雨" not in weather and "雪" not in weather
                        return {"year": year, "weather": weather, "is_sunny": is_sunny, "valid": True}
    except Exception:
        pass
    return {"year": year, "valid": False}

# 計算ボタンが押されたときの処理
if st.button("確率を計算する！", type="primary"):
    with st.spinner('気象庁の過去30年分のデータを分析中...（約5秒）'):
        start_year = 1994
        end_year = 2023
        sunny_days = 0
        valid_years = 0
        results = []
        
        # 30年分を一気に同時並行で取得して高速化
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_year_data, y, month, day) for y in range(start_year, end_year + 1)]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res["valid"]:
                    valid_years += 1
                    if res["is_sunny"]:
                        sunny_days += 1
                    results.append(res)
        
        # 結果の表示
        if valid_years > 0:
            rate = (sunny_days / valid_years) * 100
            st.success(f"🎉 **{month}月{day}日** の晴天率（雨なし）は **{rate:.1f}%** です！")
            st.write(f"過去 {valid_years} 年間で **{sunny_days} 回**、条件をクリアしました。")
            
            # 詳細データの折りたたみ表示
            with st.expander("年ごとの詳細データを見る"):
                results_sorted = sorted(results, key=lambda x: x["year"], reverse=True)
                for r in results_sorted:
                    icon = "☀️" if r["is_sunny"] else "☁️/☂️"
                    st.write(f"{r['year']}年: {r['weather']} {icon}")
        else:
            st.error("有効なデータが取得できませんでした。別の日にちをお試しください。")
