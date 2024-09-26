import streamlit as st
import pandas as pd
from datetime import datetime
from utils import get_company_info, get_stock_info, get_stock_close_price, get_major_shareholder_info

# Streamlit UI
st.title("다중 회사 정보 조회 및 비교")

# API 인증키 입력
crtfc_key = st.text_input("API 인증키 입력", type="password")

# 상장 회사 목록 CSV 파일 불러오기
df_listed = pd.read_csv('listed_corp.csv', dtype=str, encoding='utf-8')

# 사용자로부터 다중 회사명 입력 받기 (쉼표로 구분)
corp_names = st.text_area("회사명 입력 (쉼표로 구분)", "회사1, 회사2")

# 최근 5개년을 위한 연도 목록 생성
current_year = datetime.now().year
years = [str(current_year - i) for i in range(5)]

# bsns_year 선택
bsns_year = st.selectbox("사업 연도 선택", years)

# reprt_code 선택
reprt_code_options = {
    "1분기보고서": "11013",
    "반기보고서": "11012",
    "3분기보고서": "11014",
    "사업보고서": "11011"
}
reprt_code_label = st.selectbox("보고서 종류 선택", list(reprt_code_options.keys()))
reprt_code = reprt_code_options[reprt_code_label]

# 검색 버튼
search_clicked = st.button("검색")

# 검색 버튼을 누르면 검색 실행
if search_clicked and corp_names and crtfc_key:
    corp_name_list = [name.strip() for name in corp_names.split(",")]
    comparison_results = []

    for corp_name in corp_name_list:
        try:
            corp_code = df_listed.loc[df_listed['corp_name'] == corp_name, 'corp_code'].values[0]
            company_info = get_company_info(crtfc_key, corp_code)
            total_issued_stocks = get_stock_info(crtfc_key, corp_code, bsns_year, reprt_code)
            close_price = get_stock_close_price(corp_name, df_listed)

            # 추가: 최대주주 정보 가져오기
            major_shareholder_info = get_major_shareholder_info(corp_code, crtfc_key, bsns_year, reprt_code)
            company_info.update(major_shareholder_info)

            if total_issued_stocks and close_price:
                market_cap = int(total_issued_stocks.replace(',', '')) * close_price
                company_info["시가총액(억원)"] = int(market_cap / 1e8)  # 억 원 단위로 변환, 소수점 없이 저장
            else:
                company_info["시가총액(억원)"] = None

            company_info["발행주식 총수"] = total_issued_stocks if total_issued_stocks else "정보 없음"
            company_info["전일 종가"] = close_price if close_price else "정보 없음"

            comparison_results.append(company_info)

        except IndexError:
            st.error(f"해당하는 회사명을 찾을 수 없습니다: {corp_name}")
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")

    if comparison_results:
        df_comparison = pd.DataFrame(comparison_results)

        # 시가총액에 천 단위 쉼표 추가
        df_comparison["시가총액(억원)"] = df_comparison["시가총액(억원)"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "정보 없음")

        df_transposed = df_comparison.T
        st.write(f"**{len(comparison_results)}개 회사 정보 비교 결과**")
        st.dataframe(df_transposed)

        # 시가총액 비교 Bar 차트 그리기
        st.write("### 시가총액 비교 (단위: 억 원)")
        try:
            # 회사명과 시가총액을 사용하여 Bar 차트 생성
            df_filtered = df_comparison.dropna(subset=['시가총액(억원)'])  # 시가총액이 없는 회사는 제외
            df_filtered["시가총액(억원)"] = df_filtered["시가총액(억원)"].str.replace(',', '')  # 쉼표 제거
            df_filtered["시가총액(억원)"] = df_filtered["시가총액(억원)"].astype(int)  # 차트를 위한 정수 변환
            st.bar_chart(df_filtered.set_index('회사명')['시가총액(억원)'])  # Streamlit의 bar_chart를 사용
        except Exception as e:
            st.error(f"차트를 그리는 중 오류가 발생했습니다: {str(e)}")



