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
        if est_date:
            year = est_date[:4]
            month = est_date[4:6]
            day = est_date[6:8]
            return f"{year}년 {month}월 {day}일"
        return "정보 없음"

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
        "설립일": format_est_date(data.get('est_dt')),
        "법인구분": format_corp_cls(data.get('corp_cls', ''))
    }

    return company_info


# 주식 총수 정보를 가져오는 함수
def get_stock_info(crtfc_key, corp_code, bsns_year, reprt_code):
    url = "https://opendart.fss.or.kr/api/stockTotqySttus.json"
    params = {
        "crtfc_key": crtfc_key,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data and data.get('status') == '000':
        for stock in data.get('list', []):
            # '보통주' 또는 '의결권 있는 주식'인 경우에만 반환
            if stock['se'].strip() in ['보통주', '의결권 있는 주식']:
                return stock['istc_totqy']
    return None



# 전일 종가 정보를 가져오는 함수
def get_stock_close_price(corp_name, df_listed):
    try:
        stock_code = df_listed.loc[df_listed['corp_name'] == corp_name, 'stock_code'].values[0]
        yesterday = (datetime.now() - timedelta(1)).strftime("%Y%m%d")
        df = stock.get_market_ohlcv_by_date(yesterday, yesterday, stock_code)
        return df['종가'].values[0]
    except Exception:
        return None

# 최대주주 정보를 가져오는 함수
def get_major_shareholder_info(corp_code, api_key, bsns_year, reprt_code):
    url = "https://opendart.fss.or.kr/api/hyslrSttus.json"
    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        'bsns_year': bsns_year,
        'reprt_code': reprt_code,
    }

    response = requests.get(url, params=params)
    data = response.json()

    # 응답 상태 체크
    if response.status_code != 200 or data.get('status') != '000':
        return {"최대주주": "정보 없음", "보유수량": "정보 없음", "지분율": "정보 없음"}

    # 주식 종류 목록
    stock_types = ['보통주', '우선주']

    # 데이터 구조 표준화
    for item in data.get('list', []):
        stock_kind = item.get('stock_knd')
        name = item.get('nm')

        # 교환 여부를 추적하기 위한 플래그 추가
        item['swap_happened'] = False

        # stock_knd와 nm을 교환할 필요가 있는 경우 처리
        if stock_kind not in stock_types:
            if name in stock_types:
                item['stock_knd'], item['nm'] = item['nm'], item['stock_knd']
                item['swap_happened'] = True  # 교환 발생 기록

    # '보통주'만 필터링하고 '계'는 제외
    filtered_list = [item for item in data.get('list', []) if item.get('stock_knd') == '보통주' and item.get('nm') != '계']

    # 빈 리스트인 경우 처리
    if filtered_list:
        # 'trmend_posesn_stock_co' 값이 가장 큰 항목을 찾기
        max_item = max(filtered_list, key=lambda x: int(x.get('trmend_posesn_stock_co', '0').replace(',', '')))

        # 'swap_happened'가 True인 경우에만 'nm'과 'relate'를 교환
        if max_item.get('swap_happened'):
            max_item['nm'], max_item['relate'] = max_item['relate'], max_item['nm']

        # 출력할 값 정리
        max_shareholder = max_item.get('nm', '정보 없음')
        stock_amount = max_item.get('trmend_posesn_stock_co', '0')
        ownership_rate = max_item.get('trmend_posesn_stock_qota_rt', '0')

        # 숫자에 ',' 추가
        stock_amount = f"{int(stock_amount.replace(',', '')):,}"

        # 결과 반환
        return {
            "최대주주": max_shareholder,
            "보유수량": f"{stock_amount}주",
            "지분율": f"{ownership_rate}%"
        }
    else:
        return {"최대주주": "정보 없음", "보유수량": "정보 없음", "지분율": "정보 없음"}
