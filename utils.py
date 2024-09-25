import pandas as pd
import requests
from pykrx import stock
from datetime import datetime, timedelta

# DART API로부터 회사 정보를 가져오는 함수
def get_company_info(crtfc_key, corp_code):
    url = "https://opendart.fss.or.kr/api/company.json"
    params = {
        "crtfc_key": crtfc_key,
        "corp_code": corp_code
    }
    response = requests.get(url, params=params)
    data = response.json()

    def format_est_date(est_date):
        year = est_date[:4]
        month = est_date[4:6]
        day = est_date[6:8]
        return f"{year}년 {month}월 {day}일"

    def format_corp_cls(corp_cls):
        mapping = {
            'Y': '유가',
            'K': '코스닥',
            'N': '코넥스',
            'E': '기타'
        }
        return mapping.get(corp_cls, '알 수 없음')

    company_info = {
        "회사명": data.get('stock_name', ''),
        "대표이사": data.get('ceo_nm', ''),
        "주소": data.get('adres', ''),
        "설립일": format_est_date(data.get('est_dt', '')),
        "법인구분": format_corp_cls(data.get('corp_cls', ''))
    }

    return company_info

# 주식 총수 정보를 가져오는 함수
def get_stock_info(crtfc_key, corp_code):
    url = "https://opendart.fss.or.kr/api/stockTotqySttus.json"
    params = {
        "crtfc_key": crtfc_key,
        "corp_code": corp_code,
        "bsns_year": "2023",
        "reprt_code": "11011"
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data and data['status'] == '000':
        for stock in data['list']:
            if stock['se'].strip() == '보통주':
                return stock['istc_totqy']
    return None

# 전일 종가 정보를 가져오는 함수
def get_stock_close_price(corp_name, df_listed):
    stock_code = df_listed.loc[df_listed['corp_name'] == corp_name, 'stock_code'].values[0]
    yesterday = (datetime.now() - timedelta(1)).strftime("%Y%m%d")
    df = stock.get_market_ohlcv_by_date(yesterday, yesterday, stock_code)
    return df['종가'].values[0]
