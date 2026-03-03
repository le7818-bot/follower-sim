import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai
import matplotlib.font_manager as fm  # 이 부분이 fm으로 변경되었습니다.
import platform
import os

# --- 0. 한글 폰트 설정 (메모리 강제 적재 방식) ---
font_path = "NanumGothic.ttf" 

if os.path.exists(font_path):
    try:
        # [핵심] matplotlib의 폰트 매니저에 ttf 파일을 강제로 밀어 넣습니다.
        fm.fontManager.addfont(font_path)
        
        # 주입한 폰트의 이름을 가져와 전체 폰트로 설정합니다.
        font_name = fm.FontProperties(fname=font_path).get_name()
        plt.rc('font', family=font_name)
        
        # 마이너스 깨짐 방지
        plt.rcParams['axes.unicode_minus'] = False 
        
    except Exception as e:
        st.warning(f"폰트 강제 주입 중 오류가 발생했습니다: {e}")
else:
    st.warning(f"'{font_path}' 폰트 파일을 찾을 수 없습니다.")

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

# --- 3. 사이드바: 밸런스 변수 설정 (위쪽 일일 획득량 설정은 그대로 유지) ---
st.sidebar.header("🛡️ 일일 획득량 설정")
daily_base = st.sidebar.number_input("일일 확정 획득량", value=30000, step=1000)
pvp_min = st.sidebar.number_input("추가 획득 (최소)", value=5000, step=500)
pvp_max = st.sidebar.number_input("추가 획득 (최대)", value=50000, step=1000)

st.sidebar.header("📊 등급별 커트라인 설정")
st.sidebar.caption("💡 루키 1과 아이콘 값을 변경하면 중간 등급이 자동 계산됩니다! (개별 수정 가능)")

# [핵심 1] 세션 상태(메모리) 초기화
# Streamlit은 새로고침될 때마다 변수가 날아가므로, 고유 key 메모리에 값을 저장해둡니다.
if 'v_r1' not in st.session_state: st.session_state['v_r1'] = 100000
if 'v_r2' not in st.session_state: st.session_state['v_r2'] = 500000
if 'v_r3' not in st.session_state: st.session_state['v_r3'] = 1500000
if 'v_rs1' not in st.session_state: st.session_state['v_rs1'] = 3500000
if 'v_rs2' not in st.session_state: st.session_state['v_rs2'] = 6000000
if 'v_rs3' not in st.session_state: st.session_state['v_rs3'] = 8500000
if 'v_icon' not in st.session_state: st.session_state['v_icon'] = 10000000

# [핵심 2] 중간값 자동 연산 함수 (콜백)
# 최소/최대값이 변경될 때만 실행되어 중간값들을 선형(Linear)으로 균등 분배합니다.
def update_intermediates():
    min_val = st.session_state['v_r1']
    max_val = st.session_state['v_icon']
    
    if max_val > min_val:
        # 총 7단계이므로 구간(step)은 6개입니다.
        step = (max_val - min_val) / 6 
        st.session_state['v_r2'] = int(min_val + step * 1)
        st.session_state['v_r3'] = int(min_val + step * 2)
        st.session_state['v_rs1'] = int(min_val + step * 3)
        st.session_state['v_rs2'] = int(min_val + step * 4)
        st.session_state['v_rs3'] = int(min_val + step * 5)

# [핵심 3] UI 출력 (세션 상태의 key와 연결)
# 최소(v_r1)와 최대(v_icon) 입력창에만 on_change=update_intermediates 속성을 부여합니다.
v_r1 = st.sidebar.number_input("루키 1 (최소)", key='v_r1', step=50000, on_change=update_intermediates)
v_r2 = st.sidebar.number_input("루키 2", key='v_r2', step=100000)
v_r3 = st.sidebar.number_input("루키 3", key='v_r3', step=100000)
v_rs1 = st.sidebar.number_input("라이징 1(핵심보상)", key='v_rs1', step=500000)
v_rs2 = st.sidebar.number_input("라이징 2 ", key='v_rs2', step=500000)
v_rs3 = st.sidebar.number_input("라이징 3", key='v_rs3', step=500000)
v_icon = st.sidebar.number_input("아이콘 (최대/최종)", key='v_icon', step=500000, on_change=update_intermediates)

# --- 4. 밸런스 역산 로직 (Value -> Day) ---
# 최저와 최대 사이의 중간 단계 자동 연산
daily_avg = daily_base + (pvp_min + pvp_max) / 2
daily_hard = daily_base + pvp_max
daily_light = daily_base + pvp_min

# 등급 이름 및 임계값 업데이트
tier_names = ["루키 1", "루키 2", "루키 3", "라이징 1", "라이징 2", "라이징 3", "아이콘"]
threshold_vals = [v_r1, v_r2, v_r3, v_rs1, v_rs2, v_rs3, v_icon]

report_data = []
for name, val in zip(tier_names, threshold_vals):
    # 0으로 나누는 오류 방지
    hard_days = int(val / daily_hard) if daily_hard > 0 else 0
    avg_days = int(val / daily_avg) if daily_avg > 0 else 0
    light_days = int(val / daily_light) if daily_light > 0 else 0
    
    report_data.append({
        "등급": name,
        "필요 팔로워": f"{val:,}명",
        "상위 랭커(일)": hard_days,
        "평균 달성(일)": avg_days,
        "라이트(일)": light_days
    })

# --- 5. 시각화 및 데이터 출력 ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 성장 예상 곡선")
    # 그래프를 그릴 최대 일수는 라이트 유저가 아이콘을 달성하는 날 + 여유분(20일)으로 설정
    max_days = int(v_icon / daily_light) + 20 if daily_light > 0 else 100
    x = np.arange(1, max_days + 1)
    
    # [핵심 수정] np.minimum을 사용하여 계산된 값이 v_icon을 넘지 못하게 상한선(Cap) 설정
    y_light = np.minimum(x * daily_light, v_icon)
    y_hard = np.minimum(x * daily_hard, v_icon)
    y_avg = np.minimum(x * daily_avg, v_icon)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 수정된 y값들을 그래프에 적용
    ax.fill_between(x, y_light, y_hard, color='skyblue', alpha=0.1, label="성장 오차 (라이트~하드)")
    ax.plot(x, y_avg, color='blue', label="평균 성장", linewidth=3)
    
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






