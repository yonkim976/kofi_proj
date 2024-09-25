import pandas as pd
import requests
import dart_fss as dart
import json

api_key ="aca7c9a43352f3d2bd46ff80a28e2a697e9ed858"

#다트에서 리스트 가져오기
# dart.set_api_key(api_key=api_key)

# all = dart.api.filings.get_corp_code()
# df_all = pd.DataFrame(all)
# df_listed = df_all[df_all['stock_code'].notnull()]


# 기업 코드 데이터 프레임 불러오기
df_listed = pd.read_csv('listed_corp.csv', dtype=str, encoding='utf-8')

#재무제표 불러오기

corp_name = input("회사명: ")

corp_code = df_listed.loc[df_listed['corp_name']== corp_name, 'corp_code'].values[0]

# url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"

# params =  {
#     "crtfc_key" : api_key,
#     "corp_code" : corp_code,
#     "bsns_year" : "2023",
#     "reprt_code" : "11011",
#     "fs_div" :"OFS"
# }

# response = requests.get(url, params)
# data = response.json()

# if data.get("status") == "000":  # "정상" 상태 확인
#     # 리스트 형태로 재무제표 데이터 추출
#     financial_data = data.get('list', [])
    
#     # 데이터프레임으로 변환
#     df = pd.DataFrame(financial_data)
    
# df.to_excel('삼성전자 테스트.xlsx')

stock_code = df_listed.loc[df_listed['corp_name']== corp_name, 'stock_code'].values[0]

import pandas as pd
from pykrx import stock

# 조회할 종목 코드와 기간 설정
ticker = stock_code 
start_date = "20240924"
end_date = "20240924"

# 종가 데이터 조회
df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)

# 종가 데이터 출력
print(df['종가'])