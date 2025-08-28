# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# import os
# import random

# # Streamlit 페이지 설정
# st.set_page_config(page_title="생산/오류 실시간 모니터링 대시보드", layout="wide")

# # =========================
# # 1) 데이터 로드 및 전처리
# # =========================

# @st.cache_data
# def load_data(path="merge1.csv"):
#     """
#     CSV 파일을 로드하고 데이터를 전처리하는 함수.
#     파일이 존재하지 않으면 오류 메시지를 표시하고 None을 반환합니다.
#     """
#     if not os.path.exists(path):
#         st.error(f"오류: '{path}' 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")
#         return None, None
        
#     df = pd.read_csv(path)
    
#     # 날짜/시간 컬럼을 datetime 형식으로 변환
#     df["생산일자_dt"] = pd.to_datetime(df["생산일자_dt"], errors='coerce')
#     df["발생시간_dt"] = pd.to_datetime(df["발생시간_dt"], errors='coerce')
#     df["종료시간_dt"] = pd.to_datetime(df["종료시간_dt"], errors='coerce')
    
#     # NaN 값 처리 및 데이터 타입 변환
#     df["에러여부"] = df["에러여부"].fillna(0).astype(int)
#     for col in ["쿠킹스팀압력", "실링압력", "충전실온도", "실링온도", "쿠킹온도", "생산시간", "오류조치시간", "오류조치시간_재계산"]:
#         df[col] = pd.to_numeric(df[col], errors='coerce')
    
#     # 이벤트 시간 컬럼 생성
#     df["event_time"] = df["발생시간_dt"].fillna(df["생산일자_dt"])
#     df["연월"] = df["event_time"].dt.to_period("M").astype(str)
    
#     # 히트맵 및 로지스틱 회귀에 필요한 시간 변수 생성
#     df["발생_시"] = df["event_time"].dt.hour
#     df["발생_요일"] = df["event_time"].dt.dayofweek # 0:월요일, 6:일요일
    
#     # 요일/월 sin-cos 변환
#     df["요일_sin"] = np.sin(2 * np.pi * df["발생_요일"] / 7)
#     df["요일_cos"] = np.cos(2 * np.pi * df["발생_요일"] / 7)
#     df["월_sin"] = np.sin(2 * np.pi * df["event_time"].dt.month / 12)
#     df["월_cos"] = np.cos(2 * np.pi * df["event_time"].dt.month / 12)
    
#     # 생산라인 코드와 이름을 딕셔너리로 매핑
#     line_mapping = dict(zip(df["생산라인코드"], df["생산라인명"]))
    
#     return df, line_mapping

# # 작업장별 로지스틱 회귀 계수 (제공된 정보)
# LOGIT_COEFS = {
#     "W003": {"intercept": -18.7770, "실링온도": -0.8827, "쿠킹스팀압력": -11.3521, "요일_sin": -0.0444, "요일_cos": -0.1368, "월_sin": -0.0177, "월_cos": 0.1035, "순번": 0.1198},
#     "W005": {"intercept": -9.8312, "실링온도": -0.6202, "쿠킹스팀압력": -6.3627, "요일_sin": 0.0540, "요일_cos": -0.1758, "월_sin": -0.0046, "월_cos": -0.1409, "순번": -0.0140},
#     "W007": {"intercept": -12.2807, "실링온도": -0.3179, "쿠킹스팀압력": -7.4421, "요일_sin": -0.1107, "요일_cos": -0.0362, "월_sin": -0.0022, "월_cos": 0.0012, "순번": -0.0350},
#     "W002": {"intercept": -6.9799, "실링온도": 0, "쿠킹스팀압력": -4.2259, "요일_sin": -0.1545, "요일_cos": 1.2826, "월_sin": -0.1790, "월_cos": 0.3335, "순번": -0.3237}
# }

# # =========================
# # 데이터 로드 및 필터
# # =========================
# df, line_mapping = load_data()

# if df is None:
#     st.stop()

# st.sidebar.header("필터")
# date_min, date_max = df["event_time"].min().date(), df["event_time"].max().date()
# date_range = st.sidebar.date_input("기간 선택", [date_min, date_max])

# if len(date_range) == 2:
#     start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
#     filtered_df = df[(df["event_time"] >= start_date) & (df["event_time"] <= end_date)]
# else:
#     filtered_df = df.copy()

# workshops = filtered_df["작업장코드"].unique()
# sel_ws = st.sidebar.multiselect("작업장 선택", sorted(workshops), default=list(sorted(workshops)))
# if sel_ws:
#     filtered_df = filtered_df[filtered_df["작업장코드"].isin(sel_ws)]

# menu = st.sidebar.radio("메뉴 선택", ["생산/오류 현황", "공정 모니터링", "경보/실시간 로그"])

# # =========================
# # KPI 함수
# # =========================
# def display_kpis(d):
#     """주요 KPI를 계산하고 표시합니다."""
#     total_count = len(d)
#     error_count = d["에러여부"].sum()
#     error_rate = (total_count / error_count * 100) if total_count > 0 else 0
#     avg_fix_time = d.loc[d["에러여부"] == 1, "오류조치시간_재계산"].mean()

#     col1, col2, col3, col4 = st.columns(4)
#     col1.metric("전체 생산 건수", f"{total_count:,}")
#     col2.metric("오류 건수", f"{int(error_count):,}")
#     col3.metric("전체 오류율", f"{error_rate:.2f}%")
#     col4.metric("평균 오류 조치 시간", f"{avg_fix_time:.1f} 분" if pd.notna(avg_fix_time) else "-")

# # =========================
# # 생산/오류 현황 페이지
# # =========================
# if menu == "생산/오류 현황":
#     st.header("생산/오류 현황")
#     display_kpis(filtered_df)
    
#     st.markdown("---")
#     st.subheader("월별 생산/오류 건수 및 오류율 추이")
#     st.markdown("전체 생산량과 오류 건수, 그리고 그에 따른 오류율을 한 그래프에서 확인합니다.")

#     # 월별 오류 건수, 전체 생산 건수, 오류율 계산
#     monthly_errors = filtered_df.groupby("연월").agg(
#         total_count=("순번", "count"),
#         error_count=("에러여부", "sum")
#     ).reset_index()
#     monthly_errors = monthly_errors.sort_values(by="연월")
#     monthly_errors["오류율(%)"] = monthly_errors["error_count"] / monthly_errors["total_count"] * 100
    
#     # 두 개의 Y축을 가진 그래프 생성
#     fig_monthly = go.Figure()
    
#     # Y1 축 (좌측)에 전체 생산 건수 및 오류 건수 추가
#     fig_monthly.add_trace(go.Bar(x=monthly_errors["연월"], y=monthly_errors["total_count"], name="전체 생산 건수", marker_color='lightblue'))
#     fig_monthly.add_trace(go.Bar(x=monthly_errors["연월"], y=monthly_errors["error_count"], name="오류 건수", marker_color='salmon'))

#     # Y2 축 (우측)에 오류율 추가
#     fig_monthly.add_trace(go.Scatter(x=monthly_errors["연월"], y=monthly_errors["오류율(%)"], name="오류율(%)", mode='lines+markers', yaxis='y2', marker_color='darkred', line=dict(width=3)))
    
#     # 레이아웃 설정 (두 번째 Y축 추가)
#     fig_monthly.update_layout(
#         title="월별 생산/오류 건수 및 오류율",
#         xaxis_title="연월",
#         yaxis=dict(title="건수", side="left"),
#         yaxis2=dict(title="오류율(%)", overlaying="y", side="right"),
#         barmode='group',
#         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
#     )
#     st.plotly_chart(fig_monthly, use_container_width=True)
    
#     st.markdown("---")
#     st.subheader("오류 0/1 비교 - 주요 공정 변수 분포")
#     st.markdown("오류가 **발생했을 때**(1)와 **정상**(0)일 때의 주요 공정 변수 값 분포를 히스토그램으로 비교합니다.")
    
#     comparison_variables = ["충전실온도", "실링온도", "쿠킹온도", "쿠킹스팀압력", "실링압력"]
#     selected_variable = st.selectbox("비교할 변수 선택", comparison_variables, key='hist_select')
    
#     # 히스토그램 색상 개선
#     fig_hist = px.histogram(
#         filtered_df,
#         x=selected_variable,
#         color="에러여부",
#         barmode="overlay", # 막대를 겹쳐서 표시
#         title=f"{selected_variable} 분포 비교 (0: 정상, 1: 오류)",
#         labels={"에러여부": "오류 여부"},
#         color_discrete_map={"0": "darkblue", "1": "red"} # 뚜렷한 색상 대비
#     )
#     st.plotly_chart(fig_hist, use_container_width=True)

# # =========================
# # 공정 모니터링 페이지
# # =========================
# elif menu == "공정 모니터링":
#     st.header("공정 모니터링")
#     display_kpis(filtered_df)
    
#     st.markdown("---")
#     st.subheader("품목 및 생산라인별 공정 변수 모니터링")
    
#     item_options = filtered_df["품목명"].unique()
#     selected_item = st.selectbox("품목 선택", item_options)
    
#     df_item = filtered_df[filtered_df["품목명"] == selected_item]
    
#     line_options = df_item["생산라인코드"].unique()
#     selected_line = st.selectbox("생산라인 선택", line_options)
    
#     df_line = df_item[(df_item["생산라인코드"] == selected_line)]
#     normal_data = df_line[df_line["에러여부"] == 0]
    
#     if len(normal_data) > 5:
#         line_name = line_mapping.get(selected_line, "알 수 없음")
        
#         st.subheader(f"{selected_line} ({line_name}) 기준선")
        
#         mu_cook, sigma_cook = normal_data["쿠킹스팀압력"].mean(), normal_data["쿠킹스팀압력"].std()
#         mu_seal, sigma_seal = normal_data["실링압력"].mean(), normal_data["실링압력"].std()
        
#         col1, col2 = st.columns(2)
#         col1.markdown(f"**쿠킹스팀압력 μ±3σ:** {mu_cook:.2f} ± {3 * sigma_cook:.2f}")
#         col2.markdown(f"**실링압력 μ±3σ:** {mu_seal:.2f} ± {3 * sigma_seal:.2f}")

#         fig_ts = go.Figure()
        
#         # 쿠킹스팀압력 선과 기준선
#         fig_ts.add_trace(go.Scatter(x=df_line["event_time"], y=df_line["쿠킹스팀압력"], mode="lines", name="쿠킹스팀압력", line=dict(color='blue')))
#         fig_ts.add_hline(y=mu_cook, line_dash="dash", line_color="blue", name="쿠킹스팀압력 평균")
#         fig_ts.add_hline(y=mu_cook + 3 * sigma_cook, line_dash="dot", line_color="red", name="+3σ")
#         fig_ts.add_hline(y=mu_cook - 3 * sigma_cook, line_dash="dot", line_color="red", name="-3σ")
        
#         # 실링압력 선과 기준선
#         fig_ts.add_trace(go.Scatter(x=df_line["event_time"], y=df_line["실링압력"], mode="lines", name="실링압력", yaxis="y2", line=dict(color='orange')))
#         fig_ts.add_hline(y=mu_seal, line_dash="dash", line_color="darkgreen", name="실링압력 평균", yref="y2")
#         fig_ts.add_hline(y=mu_seal + 3 * sigma_seal, line_dash="dot", line_color="red", name="+3σ", yref="y2")
#         fig_ts.add_hline(y=mu_seal - 3 * sigma_seal, line_dash="dot", line_color="red", name="-3σ", yref="y2")
        
#         # 오류 발생 지점 강조 (마커 크기 및 색상 변경)
#         error_points = df_line[df_line["에러여부"] == 1]
#         if not error_points.empty:
#             fig_ts.add_trace(go.Scatter(x=error_points["event_time"], y=error_points["쿠킹스팀압력"], mode="markers", name="오류 발생 (쿠킹)", marker=dict(color="darkred", size=12, symbol='x-thin', line=dict(width=2))))
#             fig_ts.add_trace(go.Scatter(x=error_points["event_time"], y=error_points["실링압력"], mode="markers", name="오류 발생 (실링)", marker=dict(color="darkred", size=12, symbol='x-thin', line=dict(width=2)), yaxis="y2"))

#         fig_ts.update_layout(
#             title=f"{line_name} - {selected_item} 공정 변수 시계열",
#             xaxis=dict(title="시간"),
#             yaxis=dict(title="쿠킹스팀압력", side="left", showgrid=False),
#             yaxis2=dict(title="실링압력", overlaying="y", side="right", showgrid=False),
#             legend=dict(x=1.1, y=1),
#             hovermode="x unified"
#         )
#         st.plotly_chart(fig_ts, use_container_width=True)
#     else:
#         st.warning("선택한 품목 및 라인에 충분한 정상 데이터가 없습니다. 다른 항목을 선택해주세요.")

# # =========================
# # 경보/실시간 로그 페이지 (재구성)
# # =========================
# elif menu == "경보/실시간 로그":
#     st.header("경보/실시간 로그 - 실시간 감지 시뮬레이션")
#     st.markdown("작업장과 생산라인을 선택하고 '시작' 버튼을 누르면 실시간으로 공정 데이터를 감지하고 경보를 시뮬레이션합니다.")

#     # 세션 상태 초기화
#     if "data" not in st.session_state:
#         st.session_state.data = pd.DataFrame(columns=["event_time", "쿠킹스팀압력", "실링온도", "오류_감지"])
#         st.session_state.last_time = pd.Timestamp.now()
#         st.session_state.count = 0
#         st.session_state.log_messages = []
#         st.session_state.is_running = False

#     # UI 컴포넌트
#     col1, col2 = st.columns([1, 1])
#     with col1:
#         selected_ws_code = st.selectbox("작업장 선택", sorted(workshops), key='realtime_ws')
#     with col2:
#         production_lines = sorted(filtered_df[filtered_df["작업장코드"] == selected_ws_code]["생산라인코드"].unique())
#         selected_line_code = st.selectbox("생산라인 선택", production_lines, key='realtime_line')

#     col_start, col_stop, col_clear = st.columns([0.2, 0.2, 0.6])
#     with col_start:
#         if st.button("시뮬레이션 시작"):
#             st.session_state.is_running = True
#             st.session_state.log_messages.append(f"[{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}] 시뮬레이션 시작: {selected_ws_code} - {selected_line_code}")
#     with col_stop:
#         if st.session_state.is_running and st.button("시뮬레이션 정지"):
#             st.session_state.is_running = False
#             st.session_state.log_messages.append(f"[{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}] 시뮬레이션 정지")
#     with col_clear:
#         if st.button("초기화"):
#             st.session_state.is_running = False
#             st.session_state.data = pd.DataFrame(columns=["event_time", "쿠킹스팀압력", "실링온도", "오류_감지"])
#             st.session_state.last_time = pd.Timestamp.now()
#             st.session_state.count = 0
#             st.session_state.log_messages = []
            
#     # 시뮬레이션 로직
#     if 'is_running' in st.session_state and st.session_state.is_running:
#         st.info("시뮬레이션 중...")
        
#         # 기존 데이터프레임의 통계량 사용
#         normal_data_ws_line = filtered_df[
#             (filtered_df["작업장코드"] == selected_ws_code) & 
#             (filtered_df["생산라인코드"] == selected_line_code) & 
#             (filtered_df["에러여부"] == 0)
#         ]
        
#         if len(normal_data_ws_line) > 5:
#             mu_cook, sigma_cook = normal_data_ws_line["쿠킹스팀압력"].mean(), normal_data_ws_line["쿠킹스팀압력"].std()
#             mu_seal, sigma_seal = normal_data_ws_line["실링온도"].mean(), normal_data_ws_line["실링온도"].std()
            
#             # 1초마다 새로운 데이터 생성 (실제 환경처럼)
#             if st.session_state.count < 100: # 100개 데이터 생성 후 정지
#                 new_time = st.session_state.last_time + pd.Timedelta(minutes=1)
                
#                 # 정상 데이터에 약간의 노이즈 추가
#                 new_cook = np.random.normal(mu_cook, sigma_cook * 0.5)
#                 new_seal_temp = np.random.normal(mu_seal, sigma_seal * 0.5)
                
#                 # 랜덤하게 오류 유발
#                 if random.random() < 0.05: # 5% 확률로 오류 유발
#                     new_cook = np.random.normal(mu_cook + sigma_cook * 4, sigma_cook) # μ+4σ 값
#                     new_seal_temp = np.random.normal(mu_seal + sigma_seal * 4, sigma_seal) # μ+4σ 값
                
#                 # 로지스틱 회귀 모델로 오류 감지
#                 coefs = LOGIT_COEFS.get(selected_ws_code, {})
#                 features = list(coefs.keys())
#                 if "intercept" in features: features.remove("intercept")
                
#                 current_timestamp = pd.Timestamp.now()
#                 dummy_data = {
#                     "실링온도": new_seal_temp,
#                     "쿠킹스팀압력": new_cook,
#                     "요일_sin": np.sin(2 * np.pi * current_timestamp.dayofweek / 7),
#                     "요일_cos": np.cos(2 * np.pi * current_timestamp.dayofweek / 7),
#                     "월_sin": np.sin(2 * np.pi * current_timestamp.month / 12),
#                     "월_cos": np.cos(2 * np.pi * current_timestamp.month / 12),
#                     "순번": st.session_state.count
#                 }
#                 if selected_ws_code == "W002" and "실링온도" in features:
#                     features.remove("실링온도")
                    
#                 logit_score = coefs.get("intercept", 0) + sum(coefs.get(f, 0) * dummy_data.get(f, 0) for f in features)
#                 pred_prob = 1 / (1 + np.exp(-logit_score))
                
#                 # 오류 감지 여부
#                 error_detected = 1 if pred_prob > 0.5 else 0

#                 # 데이터프레임에 추가
#                 new_row = pd.DataFrame([{
#                     "event_time": new_time,
#                     "쿠킹스팀압력": new_cook,
#                     "실링온도": new_seal_temp,
#                     "오류_감지": error_detected
#                 }])
#                 st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
#                 st.session_state.last_time = new_time
#                 st.session_state.count += 1
                
#                 # 로그 메시지 추가
#                 if error_detected == 1:
#                     log_message = f"[{new_time.strftime('%H:%M:%S')}] 🚨 경보 발생! 쿠킹스팀압력: {new_cook:.2f}, 실링온도: {new_seal_temp:.2f}, 오류확률: {pred_prob:.2f}"
#                     st.session_state.log_messages.append(log_message)
#                 else:
#                     st.session_state.log_messages.append(f"[{new_time.strftime('%H:%M:%S')}] ✅ 정상: 쿠킹스팀압력: {new_cook:.2f}, 실링온도: {new_seal_temp:.2f}")

#                 # 그래프 그리기
#                 fig = go.Figure()
#                 fig.add_trace(go.Scatter(x=st.session_state.data["event_time"], y=st.session_state.data["쿠킹스팀압력"], mode='lines', name='쿠킹스팀압력', line=dict(color='blue')))
#                 fig.add_trace(go.Scatter(x=st.session_state.data["event_time"], y=st.session_state.data["실링온도"], mode='lines', name='실링온도', yaxis='y2', line=dict(color='orange')))
                
#                 # 오류 감지 지점
#                 error_points = st.session_state.data[st.session_state.data["오류_감지"] == 1]
#                 if not error_points.empty:
#                     fig.add_trace(go.Scatter(x=error_points["event_time"], y=error_points["쿠킹스팀압력"], mode="markers", name="오류 발생 (쿠킹)", marker=dict(color="red", size=10, symbol='x')))
#                     fig.add_trace(go.Scatter(x=error_points["event_time"], y=error_points["실링온도"], mode="markers", name="오류 발생 (실링)", marker=dict(color="red", size=10, symbol='x'), yaxis="y2"))

#                 fig.update_layout(
#                     title=f"실시간 공정 변수 감지 - {selected_ws_code} ({selected_line_code})",
#                     xaxis=dict(title="시간"),
#                     yaxis=dict(title="쿠킹스팀압력", side="left", showgrid=False),
#                     yaxis2=dict(title="실링온도", overlaying="y", side="right", showgrid=False),
#                     legend=dict(x=1.1, y=1),
#                     hovermode="x unified"
#                 )
#                 st.plotly_chart(fig, use_container_width=True)
                
#                 # 게이지 차트 추가
#                 st.markdown("---")
#                 st.subheader("실시간 공정 변수 현황")
                
#                 col_gauge1, col_gauge2 = st.columns(2)
#                 with col_gauge1:
#                     fig_gauge1 = go.Figure(go.Indicator(
#                         mode = "gauge+number",
#                         value = new_cook,
#                         title = {'text': "쿠킹스팀압력"},
#                         gauge = {'axis': {'range': [mu_cook-2, mu_cook+2]},
#                                  'bar': {'color': "green" if error_detected == 0 else "red"},
#                                  'steps' : [
#                                      {'range': [mu_cook - 3*sigma_cook, mu_cook + 3*sigma_cook], 'color': 'lightgray'},
#                                  ],
#                                 'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': mu_cook - 3*sigma_cook},
#                                 'bgcolor': "white",
#                                 'shape': "angular"}))
#                     st.plotly_chart(fig_gauge1, use_container_width=True)
                
#                 with col_gauge2:
#                     fig_gauge2 = go.Figure(go.Indicator(
#                         mode = "gauge+number",
#                         value = new_seal_temp,
#                         title = {'text': "실링온도"},
#                         gauge = {'axis': {'range': [mu_seal-2, mu_seal+2]},
#                                  'bar': {'color': "green" if error_detected == 0 else "red"},
#                                  'steps' : [
#                                      {'range': [mu_seal - 3*sigma_seal, mu_seal + 3*sigma_seal], 'color': 'lightgray'},
#                                  ],
#                                 'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': mu_seal - 3*sigma_seal},
#                                 'bgcolor': "white",
#                                 'shape': "angular"}))
#                     st.plotly_chart(fig_gauge2, use_container_width=True)

#                 # 로그 섹션
#                 st.markdown("---")
#                 st.subheader("실시간 로그")
#                 log_container = st.container(height=300)
#                 for log in reversed(st.session_state.log_messages):
#                     log_container.text(log)
                
#                 # 오류 발생 시 정지 버튼
#                 if error_detected == 1:
#                     st.error("🚨 오류가 감지되었습니다! 생산라인을 즉시 정지하세요.")
#                     if st.button("🚨 생산라인 정지"):
#                         st.session_state.is_running = False
#                         st.session_state.log_messages.append(f"[{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}] 생산라인 강제 정지")
#                         st.rerun()

#                 # 1초 대기 후 다시 실행
#                 import time
#                 time.sleep(1)
#                 st.rerun()

#             else:
#                 st.session_state.is_running = False
#                 st.success("시뮬레이션이 완료되었습니다. 초기화 버튼을 눌러 다시 시작하세요.")
#         else:
#             st.warning("선택한 작업장/생산라인에 충분한 정상 데이터가 없어 시뮬레이션을 시작할 수 없습니다.")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import random
import time

# Streamlit 페이지 설정
st.set_page_config(page_title="생산/오류 실시간 모니터링 대시보드", layout="wide")

# =========================
# 1) 데이터 로드 및 전처리
# =========================

@st.cache_data
def load_data(path="merge1.csv"):
    """
    CSV 파일을 로드하고 데이터를 전처리하는 함수.
    파일이 존재하지 않으면 오류 메시지를 표시하고 None을 반환합니다.
    """
    if not os.path.exists(path):
        st.error(f"오류: '{path}' 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")
        return None, None
        
    df = pd.read_csv(path)
    
    # 날짜/시간 컬럼을 datetime 형식으로 변환
    df["생산일자_dt"] = pd.to_datetime(df["생산일자_dt"], errors='coerce')
    df["발생시간_dt"] = pd.to_datetime(df["발생시간_dt"], errors='coerce')
    df["종료시간_dt"] = pd.to_datetime(df["종료시간_dt"], errors='coerce')
    
    # NaN 값 처리 및 데이터 타입 변환
    df["에러여부"] = df["에러여부"].fillna(0).astype(int)
    for col in ["쿠킹스팀압력", "실링압력", "충전실온도", "실링온도", "쿠킹온도", "생산시간", "오류조치시간", "오류조치시간_재계산"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 이벤트 시간 컬럼 생성
    df["event_time"] = df["발생시간_dt"].fillna(df["생산일자_dt"])
    df["연월"] = df["event_time"].dt.to_period("M").astype(str)
    
    # 히트맵 및 로지스틱 회귀에 필요한 시간 변수 생성
    df["발생_시"] = df["event_time"].dt.hour
    df["발생_요일"] = df["event_time"].dt.dayofweek # 0:월요일, 6:일요일
    
    # 요일/월 sin-cos 변환
    df["요일_sin"] = np.sin(2 * np.pi * df["발생_요일"] / 7)
    df["요일_cos"] = np.cos(2 * np.pi * df["발생_요일"] / 7)
    df["월_sin"] = np.sin(2 * np.pi * df["event_time"].dt.month / 12)
    df["월_cos"] = np.cos(2 * np.pi * df["event_time"].dt.month / 12)
    
    # 생산라인 코드와 이름을 딕셔너리로 매핑
    line_mapping = dict(zip(df["생산라인코드"], df["생산라인명"]))
    
    return df, line_mapping

# 작업장별 로지스틱 회귀 계수 (제공된 정보)
LOGIT_COEFS = {
    "W003": {"intercept": -18.7770, "실링온도": -0.8827, "쿠킹스팀압력": -11.3521, "요일_sin": -0.0444, "요일_cos": -0.1368, "월_sin": -0.0177, "월_cos": 0.1035, "순번": 0.1198},
    "W005": {"intercept": -9.8312, "실링온도": -0.6202, "쿠킹스팀압력": -6.3627, "요일_sin": 0.0540, "요일_cos": -0.1758, "월_sin": -0.0046, "월_cos": -0.1409, "순번": -0.0140},
    "W007": {"intercept": -12.2807, "실링온도": -0.3179, "쿠킹스팀압력": -7.4421, "요일_sin": -0.1107, "요일_cos": -0.0362, "월_sin": -0.0022, "월_cos": 0.0012, "순번": -0.0350},
    "W002": {"intercept": -6.9799, "실링온도": 0, "쿠킹스팀압력": -4.2259, "요일_sin": -0.1545, "요일_cos": 1.2826, "월_sin": -0.1790, "월_cos": 0.3335, "순번": -0.3237}
}

# =========================
# 데이터 로드 및 필터
# =========================
df, line_mapping = load_data()

if df is None:
    st.stop()

st.sidebar.header("필터")
date_min, date_max = df["event_time"].min().date(), df["event_time"].max().date()
date_range = st.sidebar.date_input("기간 선택", [date_min, date_max])

if len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered_df = df[(df["event_time"] >= start_date) & (df["event_time"] <= end_date)]
else:
    filtered_df = df.copy()

workshops = filtered_df["작업장코드"].unique()
sel_ws = st.sidebar.multiselect("작업장 선택", sorted(workshops), default=list(sorted(workshops)))
if sel_ws:
    filtered_df = filtered_df[filtered_df["작업장코드"].isin(sel_ws)]

# 메뉴 구조 변경: 사후관리 메뉴를 두 개로 분리
menu = st.sidebar.radio("메뉴 선택", ["사전관리: 실시간 감지", "사후관리: 월별 분석", "사후관리: 공정 모니터링"])

# =========================
# KPI 함수
# =========================
def display_kpis(d):
    """주요 KPI를 계산하고 표시합니다."""
    total_count = len(d)
    error_count = d["에러여부"].sum()
    error_rate = (error_count / total_count * 100) if total_count > 0 else 0
    avg_fix_time = d.loc[d["에러여부"] == 1, "오류조치시간_재계산"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("전체 생산 건수", f"{total_count:,}")
    col2.metric("오류 건수", f"{int(error_count):,}")
    col3.metric("전체 오류율", f"{error_rate:.2f}%")
    col4.metric("평균 오류 조치 시간", f"{avg_fix_time:.1f} 분" if pd.notna(avg_fix_time) else "-")

# =========================
# 사후관리: 월별 분석 페이지
# =========================
if menu == "사후관리: 월별 분석":
    st.header("사후관리: 월별 생산/오류 분석")
    st.markdown("전체 생산 데이터에 대한 분석과 오류 발생 추이를 확인합니다.")
    
    display_kpis(filtered_df)
    
    # 월별 오류 건수, 전체 생산 건수, 오류율 계산
    monthly_errors = filtered_df.groupby("연월").agg(
        total_count=("순번", "count"),
        error_count=("에러여부", "sum")
    ).reset_index()
    monthly_errors = monthly_errors.sort_values(by="연월")
    monthly_errors["오류율(%)"] = monthly_errors["error_count"] / monthly_errors["total_count"] * 100
    
    # 두 개의 Y축을 가진 그래프 생성
    fig_monthly = go.Figure()
    
    # Y1 축 (좌측)에 전체 생산 건수 및 오류 건수 추가
    fig_monthly.add_trace(go.Bar(x=monthly_errors["연월"], y=monthly_errors["total_count"], name="전체 생산 건수", marker_color='lightblue'))
    fig_monthly.add_trace(go.Bar(x=monthly_errors["연월"], y=monthly_errors["error_count"], name="오류 건수", marker_color='salmon'))

    # Y2 축 (우측)에 오류율 추가
    fig_monthly.add_trace(go.Scatter(x=monthly_errors["연월"], y=monthly_errors["오류율(%)"], name="오류율(%)", mode='lines+markers', yaxis='y2', marker_color='darkred', line=dict(width=3)))
    
    # 레이아웃 설정 (두 번째 Y축 추가)
    fig_monthly.update_layout(
        title="월별 생산/오류 건수 및 오류율",
        xaxis_title="연월",
        yaxis=dict(title="건수", side="left"),
        yaxis2=dict(title="오류율(%)", overlaying="y", side="right"),
        barmode='group',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_monthly, use_container_width=True)
    
    st.markdown("---")
    st.subheader("오류 0/1 비교 - 주요 공정 변수 분포")
    st.markdown("오류가 **발생했을 때**(1)와 **정상**(0)일 때의 주요 공정 변수 값 분포를 히스토그램으로 비교합니다.")
    
    comparison_variables = ["충전실온도", "실링온도", "쿠킹온도", "쿠킹스팀압력", "실링압력"]
    selected_variable = st.selectbox("비교할 변수 선택", comparison_variables, key='hist_select')
    
    # 히스토그램 색상 개선
    fig_hist = px.histogram(
        filtered_df,
        x=selected_variable,
        color="에러여부",
        barmode="overlay", # 막대를 겹쳐서 표시
        title=f"{selected_variable} 분포 비교 (0: 정상, 1: 오류)",
        labels={"에러여부": "오류 여부"},
        color_discrete_map={"0": "black", "1": "red"} # 뚜렷한 색상 대비
    )
    fig_hist.update_traces(opacity=1.0) # 투명도 제거
    st.plotly_chart(fig_hist, use_container_width=True)

# =========================
# 사후관리: 공정 모니터링 페이지
# =========================
elif menu == "사후관리: 공정 모니터링":
    st.header("사후관리: 품목/라인별 공정 모니터링")
    st.markdown("과거 생산 데이터를 기준으로 품목 및 생산 라인별 공정 변수의 추이를 확인합니다.")
    
    item_options = filtered_df["품목명"].unique()
    selected_item = st.selectbox("품목 선택", item_options)
    
    df_item = filtered_df[filtered_df["품목명"] == selected_item]
    
    line_options = df_item["생산라인코드"].unique()
    selected_line = st.selectbox("생산라인 선택", line_options)
    
    df_line = df_item[(df_item["생산라인코드"] == selected_line)]
    normal_data = df_line[df_line["에러여부"] == 0]
    
    if len(normal_data) > 5:
        line_name = line_mapping.get(selected_line, "알 수 없음")
        
        st.subheader(f"{selected_line} ({line_name}) 기준선")
        
        mu_cook, sigma_cook = normal_data["쿠킹스팀압력"].mean(), normal_data["쿠킹스팀압력"].std()
        mu_seal, sigma_seal = normal_data["실링압력"].mean(), normal_data["실링압력"].std()
        
        col1, col2 = st.columns(2)
        col1.markdown(f"**쿠킹스팀압력 μ±3σ:** {mu_cook:.2f} ± {3 * sigma_cook:.2f}")
        col2.markdown(f"**실링압력 μ±3σ:** {mu_seal:.2f} ± {3 * sigma_seal:.2f}")

        fig_ts = go.Figure()
        
        # 쿠킹스팀압력 선과 기준선
        fig_ts.add_trace(go.Scatter(x=df_line["event_time"], y=df_line["쿠킹스팀압력"], mode="lines", name="쿠킹스팀압력", line=dict(color='blue')))
        fig_ts.add_hline(y=mu_cook, line_dash="dash", line_color="blue", name="쿠킹스팀압력 평균")
        fig_ts.add_hline(y=mu_cook + 3 * sigma_cook, line_dash="dot", line_color="red", name="+3σ")
        fig_ts.add_hline(y=mu_cook - 3 * sigma_cook, line_dash="dot", line_color="red", name="-3σ")
        
        # 실링압력 선과 기준선
        fig_ts.add_trace(go.Scatter(x=df_line["event_time"], y=df_line["실링압력"], mode="lines", name="실링압력", yaxis="y2", line=dict(color='orange')))
        fig_ts.add_hline(y=mu_seal, line_dash="dash", line_color="darkgreen", name="실링압력 평균", yref="y2")
        fig_ts.add_hline(y=mu_seal + 3 * sigma_seal, line_dash="dot", line_color="red", name="+3σ", yref="y2")
        fig_ts.add_hline(y=mu_seal - 3 * sigma_seal, line_dash="dot", line_color="red", name="-3σ", yref="y2")
        
        # 오류 발생 지점 강조 (마커 크기 및 색상 변경)
        error_points = df_line[df_line["에러여부"] == 1]
        if not error_points.empty:
            fig_ts.add_trace(go.Scatter(x=error_points["event_time"], y=error_points["쿠킹스팀압력"], mode="markers", name="오류 발생 (쿠킹)", marker=dict(color="darkred", size=12, symbol='x-thin', line=dict(width=2))))
            fig_ts.add_trace(go.Scatter(x=error_points["event_time"], y=error_points["실링압력"], mode="markers", name="오류 발생 (실링)", marker=dict(color="darkred", size=12, symbol='x-thin', line=dict(width=2)), yaxis="y2"))

        fig_ts.update_layout(
            title=f"{line_name} - {selected_item} 공정 변수 시계열",
            xaxis=dict(title="시간"),
            yaxis=dict(title="쿠킹스팀압력", side="left", showgrid=False),
            yaxis2=dict(title="실링압력", overlaying="y", side="right", showgrid=False),
            legend=dict(x=1.1, y=1),
            hovermode="x unified"
        )
        st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.warning("선택한 품목 및 라인에 충분한 정상 데이터가 없습니다. 다른 항목을 선택해주세요.")

# =========================
# 사전관리: 실시간 감지 페이지
# =========================
elif menu == "사전관리: 실시간 감지":
    st.header("사전관리: 실시간 감지 - 실시간 감지 시뮬레이션")
    st.markdown("작업장과 생산라인을 선택하고 '시작' 버튼을 누르면 실시간으로 공정 데이터를 감지하고 경보를 시뮬레이션합니다.")

    # 세션 상태 초기화
    if "is_initialized" not in st.session_state or "clear_state" in st.session_state:
        st.session_state.is_initialized = True
        st.session_state.data = pd.DataFrame(columns=["event_time", "쿠킹스팀압력", "실링온도", "오류_감지"])
        st.session_state.last_time = pd.Timestamp.now()
        st.session_state.count = 0
        st.session_state.log_messages = []
        st.session_state.is_running = False
        if "clear_state" in st.session_state:
            del st.session_state["clear_state"]

    # UI 컴포넌트
    col1, col2 = st.columns([1, 1])
    with col1:
        selected_ws_code = st.selectbox("작업장 선택", sorted(workshops), key='realtime_ws')
    with col2:
        production_lines = sorted(filtered_df[filtered_df["작업장코드"] == selected_ws_code]["생산라인코드"].unique())
        selected_line_code = st.selectbox("생산라인 선택", production_lines, key='realtime_line')

    col_start, col_stop, col_clear = st.columns([0.2, 0.2, 0.6])
    with col_start:
        if st.button("시뮬레이션 시작"):
            st.session_state.is_running = True
            st.session_state.log_messages.append(f"[{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}] 시뮬레이션 시작: {selected_ws_code} - {selected_line_code}")
    with col_stop:
        if st.session_state.is_running and st.button("시뮬레이션 정지"):
            st.session_state.is_running = False
            st.session_state.log_messages.append(f"[{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}] 시뮬레이션 정지")
    with col_clear:
        if st.button("초기화"):
            st.session_state["clear_state"] = True
            st.rerun()
            
    # 시뮬레이션 로직
    if 'is_running' in st.session_state and st.session_state.is_running:
        st.info("시뮬레이션 중...")
        
        # 기존 데이터프레임의 통계량 사용
        normal_data_ws_line = filtered_df[
            (filtered_df["작업장코드"] == selected_ws_code) & 
            (filtered_df["생산라인코드"] == selected_line_code) & 
            (filtered_df["에러여부"] == 0)
        ]
        
        if len(normal_data_ws_line) > 5:
            mu_cook, sigma_cook = normal_data_ws_line["쿠킹스팀압력"].mean(), normal_data_ws_line["쿠킹스팀압력"].std()
            mu_seal, sigma_seal = normal_data_ws_line["실링온도"].mean(), normal_data_ws_line["실링온도"].std()
            
            new_time = st.session_state.last_time + pd.Timedelta(minutes=1)
            
            # 정상 데이터에 약간의 노이즈 추가
            new_cook = np.random.normal(mu_cook, sigma_cook * 0.5)
            new_seal_temp = np.random.normal(mu_seal, sigma_seal * 0.5)
            
            # 오류 유발 조건 (20% 확률)
            error_detected = 0
            if random.random() < 0.20:
                # 쿠킹스팀압력을 23 이하로 강제 설정하여 오류 유발
                new_cook = 22.5
                error_detected = 1
            
            # 로지스틱 회귀 모델로 오류 감지
            coefs = LOGIT_COEFS.get(selected_ws_code, {})
            features = list(coefs.keys())
            if "intercept" in features: features.remove("intercept")
            
            current_timestamp = pd.Timestamp.now()
            dummy_data = {
                "실링온도": new_seal_temp,
                "쿠킹스팀압력": new_cook,
                "요일_sin": np.sin(2 * np.pi * current_timestamp.dayofweek / 7),
                "요일_cos": np.cos(2 * np.pi * current_timestamp.dayofweek / 7),
                "월_sin": np.sin(2 * np.pi * current_timestamp.month / 12),
                "월_cos": np.cos(2 * np.pi * current_timestamp.month / 12),
                "순번": st.session_state.count
            }
            if selected_ws_code == "W002" and "실링온도" in features:
                features.remove("실링온도")
                
            logit_score = coefs.get("intercept", 0) + sum(coefs.get(f, 0) * dummy_data.get(f, 0) for f in features)
            pred_prob = 1 / (1 + np.exp(-logit_score))
            
            # 최종 오류 감지 여부
            if pred_prob > 0.5:
                error_detected = 1

            # 데이터프레임에 추가
            new_row = pd.DataFrame([{
                "event_time": new_time,
                "쿠킹스팀압력": new_cook,
                "실링온도": new_seal_temp,
                "오류_감지": error_detected
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            st.session_state.last_time = new_time
            st.session_state.count += 1
            
            # 오류 발생 시 경고 메시지를 상단에 표시하고 시뮬레이션 중지
            if error_detected == 1:
                st.session_state.is_running = False
                st.error("🚨🚨 에러 발생! 시뮬레이션을 중지합니다. 🚨🚨")

            # 로그 메시지 추가
            if error_detected == 1:
                log_message = f"[{new_time.strftime('%H:%M:%S')}] 🚨🚨 에러!! 에러!! 쿠킹스팀압력: {new_cook:.2f}, 실링온도: {new_seal_temp:.2f}, 오류확률: {pred_prob:.2f}"
                st.session_state.log_messages.append(log_message)
            else:
                st.session_state.log_messages.append(f"[{new_time.strftime('%H:%M:%S')}] ✅ 정상: 쿠킹스팀압력: {new_cook:.2f}, 실링온도: {new_seal_temp:.2f}")
                
            # 그래프 그리기
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=st.session_state.data["event_time"], y=st.session_state.data["쿠킹스팀압력"], mode='lines', name='쿠킹스팀압력', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=st.session_state.data["event_time"], y=st.session_state.data["실링온도"], mode='lines', name='실링온도', yaxis='y2', line=dict(color='orange')))
            
            # 오류 감지 지점
            error_points = st.session_state.data[st.session_state.data["오류_감지"] == 1]
            if not error_points.empty:
                fig.add_trace(go.Scatter(x=error_points["event_time"], y=error_points["쿠킹스팀압력"], mode="markers", name="오류 발생 (쿠킹)", marker=dict(color="red", size=10, symbol='x')))
                fig.add_trace(go.Scatter(x=error_points["event_time"], y=error_points["실링온도"], mode="markers", name="오류 발생 (실링)", marker=dict(color="red", size=10, symbol='x'), yaxis="y2"))

            fig.update_layout(
                title=f"실시간 공정 변수 감지 - {selected_ws_code} ({selected_line_code})",
                xaxis=dict(title="시간"),
                yaxis=dict(title="쿠킹스팀압력", side="left", showgrid=False),
                yaxis2=dict(title="실링온도", overlaying="y", side="right", showgrid=False),
                legend=dict(x=1.1, y=1),
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 게이지 차트 추가
            st.markdown("---")
            st.subheader("실시간 공정 변수 현황")
            
            col_gauge1, col_gauge2 = st.columns(2)
            with col_gauge1:
                fig_gauge1 = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = new_cook,
                    title = {'text': "쿠킹스팀압력"},
                    gauge = {'axis': {'range': [mu_cook-2, mu_cook+2]},
                             'bar': {'color': "green" if error_detected == 0 else "red"},
                             'steps' : [
                                 {'range': [mu_cook - 3*sigma_cook, mu_cook + 3*sigma_cook], 'color': 'lightgray'},
                             ],
                            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': mu_cook - 3*sigma_cook},
                            'bgcolor': "white",
                            'shape': "angular"}))
                st.plotly_chart(fig_gauge1, use_container_width=True)
            
            with col_gauge2:
                fig_gauge2 = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = new_seal_temp,
                    title = {'text': "실링온도"},
                    gauge = {'axis': {'range': [mu_seal-2, mu_seal+2]},
                             'bar': {'color': "green" if error_detected == 0 else "red"},
                             'steps' : [
                                 {'range': [mu_seal - 3*sigma_seal, mu_seal + 3*sigma_seal], 'color': 'lightgray'},
                             ],
                            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': mu_seal - 3*sigma_seal},
                            'bgcolor': "white",
                            'shape': "angular"}))
                st.plotly_chart(fig_gauge2, use_container_width=True)

            # 로그 섹션
            st.markdown("---")
            st.subheader("실시간 로그")
            log_container = st.container(height=300)
            for log in reversed(st.session_state.log_messages):
                log_container.text(log)
            
            if st.session_state.is_running: # 시뮬레이션이 계속 실행 중일 때만
                time.sleep(1)
                st.rerun()

        else:
            st.warning("선택한 작업장/생산라인에 충분한 정상 데이터가 없어 시뮬레이션을 시작할 수 없습니다.")

