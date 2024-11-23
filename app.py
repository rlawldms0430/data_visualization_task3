#C190010 김지은

import streamlit as st  # Streamlit 라이브러리
import geopandas as gpd  # GeoPandas
import pandas as pd  # Pandas
import folium  # 지도 라이브러리
from streamlit_folium import st_folium  # Streamlit과 Folium 통합

# 앱 제목
st.title("Regional Birth Rate Choropleth Map")
st.write("This app visualizes birth rates by region using a choropleth map.")

# Step 1: 합계출산율 엑셀 파일 불러오기
st.write("### Step 1: Load Birth Rate Data")

try:
    # 엑셀 데이터 로드
    birth_data = pd.read_excel('./합계출산율.xlsx',header=[0, 1])
    # 필요한 컬럼만 선택
    birth_data = birth_data[[('행정구역별', '행정구역별'), ('2023', '합계출산율 (가임여성 1명당 명)')]]

    birth_data.columns = ['시군구명', '출산율']  # 컬럼 이름 정리

    # 출산율 데이터 타입 변환
    birth_data['출산율'] = birth_data['출산율'].astype(float)

    # '전국' 항목 제거
    birth_data = birth_data[birth_data['시군구명'] != '전국']

    # 시군구명 이름 매핑
    name_mapping = {
        '강원특별자치도': '강원도',
        '제주특별자치도': '제주특별자치도'
    }
    birth_data['시군구명'] = birth_data['시군구명'].replace(name_mapping)

    # 데이터 출력
    st.write("Birth Rate Data:")
    st.dataframe(birth_data.head())
except Exception as e:
    st.error(f"Error loading birth rate data: {e}")


# Step 2: 한국 시도 GeoJSON 데이터 불러오기
st.write("### Step 2: Load GeoJSON Data")
geojson_path = './TL_SCCO_CTPRVN.json'

try:
    # GeoJSON 데이터 로드
    korea_sido = gpd.read_file(geojson_path)
    st.write("GeoJSON Data:")
    st.write(korea_sido.head())

    # 좌표계 확인
    st.write(f"Current CRS: {korea_sido.crs}") #4326

    # 좌표계를 EPSG:5179으로 변환 (UTM-K)
    if korea_sido.crs != "EPSG:5179":
        korea_5179 = korea_sido.to_crs(epsg=5179, inplace=False)
        st.write("Coordinate Reference System (CRS) converted to EPSG:5179")
    else:
        korea_5179 = korea_sido
        st.write("Coordinate Reference System (CRS) is already EPSG:5179")

    st.write("Converted GeoJSON Data Preview:")
    st.write(korea_5179.head())
except Exception as e:
    st.error(f"Error loading GeoJSON data: {e}")



# Step 3: 데이터 병합
st.write("### Step 3: Merge Data")
try:
    # GeoJSON 데이터와 출산율 데이터 병합
    geo_merged = korea_sido.merge(
        birth_data,
        left_on='CTP_KOR_NM',  # GeoJSON 데이터의 행정구역 이름
        right_on='시군구명',    # 출산율 데이터의 행정구역 이름
        how='left'             # 병합 방식: GeoJSON 기준 병합
    )

    # 병합 후 누락된 데이터 확인
    missing_data = geo_merged[geo_merged['출산율'].isna()]
    if not missing_data.empty:
        st.warning("Some regions are missing birth rate data:")
        st.write(missing_data[['CTP_KOR_NM']])

    st.write("Merged Data Preview:")
    st.dataframe(geo_merged[['CTP_KOR_NM', '출산율']].head())
except Exception as e:
    st.error(f"Error merging data: {e}")


# Step 4: Folium 지도 생성
st.write("### Step 4: Display Choropleth Map")
try:
    # Folium 지도 생성
    m = folium.Map(location=[36.5, 127.5], zoom_start=7)

    # Choropleth 추가
    folium.Choropleth(
        geo_data=geo_merged.to_json(),  # GeoPandas 객체를 JSON으로 변환
        data=geo_merged,               # 병합된 데이터 사용
        columns=['CTP_KOR_NM', '출산율'],  # 지역 이름과 출산율 컬럼 지정
        key_on='feature.properties.CTP_KOR_NM',  # GeoJSON에서 지역 이름과 매칭
        fill_color='YlGnBu',  # 색상 팔레트
        fill_opacity=0.7,  # 투명도
        line_opacity=0.2,  # 경계선 투명도
        legend_name='출산율',  # 범례 이름
    ).add_to(m)

    # Streamlit에서 Folium 지도 표시
    st_folium(m, width=800, height=600)
except Exception as e:
    st.error(f"Error displaying map: {e}")
