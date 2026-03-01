import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai
import matplotlib
from matplotlib import font_manager, rc
import platform

# --- 1. 환경 설정 (수정된 깃허브 업로드 버전) ---
try:
    # [중요] 깃허브에는 아래 변수를 비워둔 채로 올리세요!
    MY_LOCAL_KEY = "" 

    # 1. 로컬 변수가 비어있다면 스트림릿 서버의 'Secrets' 금고를 확인합니다.
    if not MY_LOCAL_KEY:
        try:
            # Streamlit Cloud 설정 창에 입력한 키를 가져옵니다.
            API_KEY = st.secrets["GEMINI_API_KEY"]
        except:
            API_KEY = ""
    else:
        API_KEY = MY_LOCAL_KEY

    if API_KEY:
        clean_key = "".join(API_KEY.split())
        genai.configure(api_key=clean_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
    else:
        # 키가 없을 때 사용자에게 보여줄 메시지
        st.error("⚠️ API 키 설정이 필요합니다. Streamlit Cloud의 Secrets 설정을 확인해 주세요.")

except Exception as e:
    st.error(f"⚠️ 시스템 초기화 중 오류 발생: {str(e)}")

# --- 2. UI 구성 ---
st.set_page_config(page_title="팔로워:수치 제어 시뮬레이터", layout="wide")
st.title("🌟 팔로워 시스템: 수치 기반 통합 시뮬레이터")
st.markdown("> **본 시뮬레이터의 수치는 임의의 가상 데이터입니다.**")

# --- 3. 사이드바: 밸런스 변수 설정 ---
st.sidebar.header("🛡️ 일일 획득량 설정")
daily_base = st.sidebar.slider("일일 확정 획득량", 10000, 100000, 30000, step=5000)
pvp_min = st.sidebar.slider("추가 획득 (최소)", 0, 50000, 5000)
pvp_max = st.sidebar.slider("추가 획득 (최대)", 5000, 200000, 50000)

st.sidebar.header("📊 등급별 커트라인 설정 (직접 입력)")
# 주연님이 원하시는 '예쁜 숫자'로 직접 수정 가능합니다.
v_r2 = st.sidebar.number_input("루키 2", value=500000, step=100000)
v_r3 = st.sidebar.number_input("루키 3", value=1500000, step=100000)
v_rs1 = st.sidebar.number_input("라이징 1", value=3500000, step=500000)
v_rs2 = st.sidebar.number_input("라이징 2 (핵심보상)", value=6000000, step=500000)
v_rs3 = st.sidebar.number_input("라이징 3", value=8500000, step=500000)
v_icon = st.sidebar.number_input("아이콘 (최종)", value=10000000, step=500000)

# --- 4. 밸런스 역산 로직 (Value -> Day) ---
daily_avg = daily_base + (pvp_min + pvp_max) / 2
daily_hard = daily_base + pvp_max
daily_light = daily_base + pvp_min

tier_names = ["루키 2", "루키 3", "라이징 1", "라이징 2", "라이징 3", "아이콘"]
threshold_vals = [v_r2, v_r3, v_rs1, v_rs2, v_rs3, v_icon]

report_data = []
for name, val in zip(tier_names, threshold_vals):
    report_data.append({
        "등급": name,
        "필요 팔로워": f"{val:,}명",
        "상위 랭커(일)": int(val / daily_hard),
        "평균 달성(일)": int(val / daily_avg),
        "라이트(일)": int(val / daily_light)
    })

# --- 5. 시각화 및 데이터 출력 ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 성장 예상 곡선")
    max_days = int(v_icon / daily_light) + 10
    x = np.arange(1, max_days + 1)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.fill_between(x, x * daily_light, x * daily_hard, color='skyblue', alpha=0.1, label="성장 오차")
    ax.plot(x, x * daily_avg, color='blue', label="평균 성장", linewidth=3)
    
    for name, val in zip(tier_names, threshold_vals):
        ax.axhline(y=val, color='gray', linestyle=':', alpha=0.5)
        ax.text(1, val, f" {name}", fontsize=10, verticalalignment='bottom')

    ax.set_xlabel("플레이 일차 (Day)")
    ax.set_ylabel("누적 팔로워")
    ax.legend()
    ax.grid(True, axis='y', alpha=0.2)
    st.pyplot(fig)

with col2:
    st.subheader("📋 밸런스 리포트")
    df = pd.DataFrame(report_data)
    st.table(df)
    
    # CSV 다운로드 기능
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 CSV로 내보내기", csv, "balance_table.csv", "text/csv")

# --- 6. AI 진단 ---
st.divider()
if st.button("✨ AI 리드 기획자 진단 받기"):
    with st.spinner("분석 중..."):
        try:
            prompt = f"""
            너는 밸런스 시스템 기획자야. 아래 데이터를 보고 밸런스를 평가해.
            [데이터] {report_data}
            [요구사항] 
                        2. 라이징 2(메인보상) 구간의 도달 시점이 리텐션 확보에 유리한가?
            3. 문체는 정중하고 날카로운 개조식으로 작성할 것.

            1. 🚨 **이탈 위험 구간 (Churn Point) 분석**: 등급 간 소요일 간격을 볼 때, 유저가 가장 지루함을 느끼고 이탈할 위험이 큰 '폐사 구간'이 어디인지 데이터를 근거로 지적해 줘.
            2. 🎁 **보상 배치 및 구조 제안**: "초반 등급 달성 일자를 낮게 잡아 메인 보상을 일찍 획득하게 하고 (Front-loading), 후반 다이아몬드까지는 온전히 유저의 애정을 투자하게 하는 방안" 등 수치에 맞는 보상 기획적 대안을 구체적으로 제시해 줘.
            3. ⚔️ **격차 평가**: 랭커와 라이트 유저의 도달일 격차가 게임 생태계에 미칠 영향을 분석하고, PVP 보상의 비중이 적절한지 평가해 줘.
            4. 수정이 필요해 보이는 부분은 정확한 수치를 제안해줘. 제안 시 이렇게 했을때의 장점과 단점을 추가해줘.
            
            문체는 정중하지만 날카롭고 전문적으로 작성해. 간결한 문장을 사용해서 눈에 확 들어오게 작성해.
                "모든 피드백은 '개선 포인트' 위주의 불렛포인트로 작성할 것."

                "서술형 문장을 지양하고, '~임', '~함'과 같은 개조식 문체를 사용해."

                "가장 시급한 수정 사항에는 [CRITICAL] 머리말을 붙여줘."
            """
            response = model.generate_content(prompt)
            st.write(response.text)
        except Exception as e:

            st.error(f"AI 호출 실패: {e}")



