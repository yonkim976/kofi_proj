import pandas as pd
import requests
from pykrx import stock
from datetime import datetime, timedelta

### 기업개황
def get_company_info(crtfc_key, corp_code):
    
    all_ind_code = pd.read_csv('industry_code.csv', dtype=str)
    url = "https://opendart.fss.or.kr/api/company.json"
    params = {
        "crtfc_key": crtfc_key,
        "corp_code": corp_code
    }
    response = requests.get(url, params=params)
    data = response.json()

    # 설립일 형식 변환 함수
    def format_est_date(est_date):
        if est_date:
            year = est_date[:4]
            month = est_date[4:6]
            day = est_date[6:8]
            return f"{year}년 {month}월 {day}일"
        return "정보 없음"

    # 법인 구분 변환 함수
    def format_corp_cls(corp_cls):
        mapping = {
            'Y': '유가',
            'K': '코스닥',
            'N': '코넥스',
            'E': '기타'
        }
        return mapping.get(corp_cls, '알 수 없음')

    # 산업 분류 찾기 함수
    def get_industry_name(ind_code, all_ind_code):
        try:
            industry_name = all_ind_code.loc[all_ind_code['산업코드'] == ind_code, '분류'].values[0]
            return industry_name
        except IndexError:
            return "산업 분류를 찾을 수 없음"

    # 산업코드 가져오기
    ind_code = data.get('induty_code', '')

    # 회사 정보 구성
    company_info = {
        "회사명": data.get('stock_name', ''),
        "대표이사": data.get('ceo_nm', ''),
        "주소": data.get('adres', ''),
        "설립일": format_est_date(data.get('est_dt')),
        "법인구분": format_corp_cls(data.get('corp_cls', '')),
        "산업분류": get_industry_name(ind_code, all_ind_code)  # 산업 분류 추가
    }

    return company_info

### 발행주식
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

### 시가총액  
def get_stock_close_price(corp_name, df_listed):
    # 주말과 공휴일을 고려한 이전 거래일 계산 함수
    def get_previous_business_day():
        date = datetime.now() - timedelta(1)
        while date.weekday() >= 5:  # 5: Saturday, 6: Sunday
            date -= timedelta(1)
        return date.strftime("%Y%m%d")
    
    try:
        # df_listed에서 기업명을 기준으로 주식 코드를 찾음
        stock_code = df_listed.loc[df_listed['corp_name'] == corp_name, 'stock_code'].values[0]
        
        # 이전 거래일 계산
        previous_business_day = get_previous_business_day()
        
        # 주식 종가 데이터를 가져옴
        df = stock.get_market_ohlcv_by_date(previous_business_day, previous_business_day, stock_code)
        
        # 종가 값을 반환
        return df['종가'].values[0]
    except IndexError:
        print(f"Error: {corp_name} not found in df_listed.")
        return None
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return None

### 최대주주
def get_major_shareholder_info(corp_code, crtfc_key, bsns_year, reprt_code):
    """
    기업 이름을 받아서 최대주주, 보유수량, 지분율을 반환하는 함수
    
    Parameters:
    corp_name (str): 기업 이름
    api_key (str): DART API 인증키
    bsns_year (str): 사업연도 (기본값: '2023')
    reprt_code (str): 보고서 코드 (기본값: '11011' - 사업보고서)
    df_listed (DataFrame): 기업 고유번호가 포함된 DataFrame

    Returns:
    dict: 최대주주 정보 (최대주주, 보유수량, 지분율)
    """   
    url = "https://opendart.fss.or.kr/api/hyslrSttus.json"
    params = {
        "crtfc_key": crtfc_key,
        "corp_code": corp_code,
        'bsns_year': bsns_year,
        'reprt_code': reprt_code,
    }

    # API 호출
    response = requests.get(url, params=params)
    data = response.json()

    # 주식 종류 목록
    stock_types = ['보통주', '우선주', '의결권 있는 주식']

    # 데이터 구조 표준화
    for item in data.get('list', []):
        stock_kind = item.get('stock_knd')
        name = item.get('nm')

        # 교환 여부를 추적하기 위한 플래그 추가
        item['swap_happened'] = False

        # stock_knd와 nm을 교환할 필요가 있는 경우 처리
        if stock_kind not in ['보통주', '우선주','의결권 있는 주식']:
            if name in ['보통주', '우선주','의결권 있는 주식']:
                item['stock_knd'], item['nm'] = item['nm'], item['stock_knd']
                item['swap_happened'] = True  # 교환 발생 기록

    # '보통주', '의결권 있는 주식'을 필터링하고 '계'는 제외
    filtered_list = [
        item for item in data.get('list', [])
        if item.get('stock_knd') in ['보통주', '의결권 있는 주식'] and item.get('nm') != '계'
    ]


    # 빈 리스트인 경우 처리
    if filtered_list:
        # 'trmend_posesn_stock_co' 값이 가장 큰 항목을 찾기
        max_item = max(filtered_list, key=lambda x: int(x.get('trmend_posesn_stock_co', '0').replace(',', '')))

        # 'swap_happened'가 True인 경우에만 'nm'과 'relate'를 교환
        if max_item.get('swap_happened'):
            max_item['nm'], max_item['relate'] = max_item['relate'], max_item['nm']

        # 출력할 값 정리
        max_shareholder = max_item['nm']
        stock_amount = max_item['trmend_posesn_stock_co']
        ownership_rate = max_item['trmend_posesn_stock_qota_rt']

        # 숫자에 ',' 추가
        stock_amount = f"{int(stock_amount.replace(',', '')):,}"

        # 결과 반환
        return {
            "최대주주": max_shareholder,
            "보유수량": f"{stock_amount}주",
            "지분율": f"{ownership_rate}%"
        }
    else:
        return {"message": "필터링된 데이터가 없습니다."}

### 재무정보
def get_financial_statements(corp_code, crtfc_key, bsns_year, reprt_code, fs_div):
    """
    기업의 주요 재무 정보를 가져오는 함수

    Parameters:
    - corp_code (str): 기업 고유번호
    - api_key (str): DART API 인증키
    - bsns_year (str): 사업 연도
    - reprt_code (str): 보고서 코드
    - fs_div (str): 재무제표 구분 ('CFS': 연결재무제표, 'OFS': 재무제표). 기본값은 'CFS'입니다.

    Returns:
    - dict: 주요 재무 항목과 그 값이 담긴 딕셔너리
    """
    fnlttAll_url = 'https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json'
    params = {
        "crtfc_key": crtfc_key,        # 인증키
        "corp_code": corp_code,      # 회사 코드
        "bsns_year": bsns_year,      # 연도
        "reprt_code": reprt_code,    # 보고서 코드
        "fs_div": fs_div             # 연결/별도 구분 ('CFS': 연결재무제표, 'OFS': 별도재무제표)
    }

    # 천 단위 콤마 추가 함수
    def format_number(value):
        if value and value.replace(',', '').replace('-', '').isdigit():
            return f"{int(value.replace(',', '')):,}"
        else:
            return "정보 없음"

    # 주요 항목을 추출하고 포맷하는 함수
    def get_financial_data(data_list, account_id):
        for item in data_list:
            if item.get('account_id') == account_id:
                return format_number(item.get('thstrm_amount'))
        return "정보 없음"

    # fnlttAll 데이터 요청
    response_fnlttAll = requests.get(fnlttAll_url, params=params)
    data_fnlttAll = response_fnlttAll.json()

    # 결과 확인 및 필요한 데이터 추출
    if data_fnlttAll.get('status') == '000':
        data_list = data_fnlttAll.get('list', [])

        # 주요 항목별 데이터 추출 및 반환
        financial_items = {
            "매출액": "ifrs-full_Revenue",
            "매출원가": "ifrs-full_CostOfSales",
            "영업이익": "dart_OperatingIncomeLoss",
            "당기순이익": "ifrs-full_ProfitLoss",
            "자산총계": "ifrs-full_Assets",
            "현금및현금성자산": "ifrs-full_CashAndCashEquivalents",
            "부채총계": "ifrs-full_Liabilities",
            "사채": "ifrs-full_NoncurrentPortionOfNoncurrentBondsIssued",
            "자본총계": "ifrs-full_Equity"
        }

        financial_data = {}
        for label, account_id in financial_items.items():
            value = get_financial_data(data_list, account_id)
            financial_data[label] = value

        return financial_data
    else:
        return {"message": "API 호출 실패 또는 데이터를 찾을 수 없습니다."}
