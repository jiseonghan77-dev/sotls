import streamlit as st
import pandas as pd
import itertools
import math
import time
from google import genai
import os

st.set_page_config(page_title="너 이 생기부로 어디갈래?", page_icon="🎓", layout="wide")

st.title("🎓 너 이 생기부로 어디갈래?")

subjects = { # 과목 목록
    1: {
        1: {"공통": ["공통국어1", "공통수학1", "공통영어1", "통합사회1", "통합과학1", "한국사1"]},
        2: {"공통": ["공통국어2", "공통수학2", "공통영어2", "통합사회2", "통합과학2", "한국사2"]}
    },
    2: {
        1: {
            "공통": ["문학", "대수", "영어1", "중국어"],
            "선택": ["물리학", "화학", "생명과학", "지구과학", "세계시민과 지리", "세계사", "사회와 문화", "현대사회와 윤리"]
        },
        2: {
            "공통": ["화법과 언어", "미적분1", "영어2", "중국어 회화"],
            "선택": ["독서 토론과 글쓰기", "경제 수학", "기하", "역학과 에너지", "물질과 에너지", "세포와 물질대사", "지구시스템과학", "도시의 미래 탐구", "동아시아 역사 기행", "정치", "경제", "윤리와 사상"]
        }
    },
    3: {
        1: {
            "공통": ["독서와 작문", "확률과 통계", "영어 독해와 작문", "인공지능 기초"],
            "선택": ["주제 탐구 독서", "미적분2", "미디어 영어", "한국지리 탐구", "법과 사회", "국제 관계의 이해", "인문학과 윤리", "전자기와 양자", "화학 반응의 세계", "생물의 유전", "행성우주과학"]
        }
    }
}

selection_rules = {1: {1: 0, 2: 0}, 2: {1: 3, 2: 4}, 3: {1: 4}}

def grade9(rank, total):
    percent = rank / total * 100
    if percent <= 4: return 1
    elif percent <= 11: return 2
    elif percent <= 23: return 3
    elif percent <= 40: return 4
    elif percent <= 60: return 5
    elif percent <= 77: return 6
    elif percent <= 89: return 7
    elif percent <= 96: return 8
    else: return 9
    
def grade5(rank, total):
    percent = rank / total * 100
    if percent <= 10: return 1
    elif percent <= 34: return 2
    elif percent <= 66: return 3
    elif percent <= 90: return 4
    else: return 5

def find_rank_for_grade(total_students, target_grade):
    for rank in range(1, total_students + 1):
        if grade5(rank, total_students) == target_grade:
            return rank
    return total_students

def required_rank_change(row, target_grade):
    current_rank = int(row["등수"])
    total_students = int(row["수강자수"])
    target_rank = find_rank_for_grade(total_students, target_grade)
    change = current_rank - target_rank
    return max(0, change)

# Session State 초기화
if "step" not in st.session_state: 
    st.session_state.step = 0

if "analysis_type" not in st.session_state:
    st.session_state.analysis_type = None

if "analysis_level" not in st.session_state:
    st.session_state.analysis_level = None

# Step 0: 메인 화면
if st.session_state.step == 0:
    st.subheader("원하는 기능을 선택하세요")

    menu1, menu2 = st.columns(2)

    with menu1:
        if st.button("📈 성적 계산", use_container_width=True):
            st.session_state.analysis_type = "grade"
            st.session_state.step = 1
            st.rerun()

    with menu2:
        if st.button("📚 생기부 분석", use_container_width=True):
            st.session_state.analysis_type = "school_record"
            st.session_state.step = 10
            st.rerun()

# Step 1: 학년 & 학기 선택
elif st.session_state.step == 1:
    st.header("1️⃣ 학년 및 학기 선택")
    grade = st.selectbox("학년 선택", [1, 2, 3])

    if grade == 3:
        semester = 1
    else:
        semester = st.selectbox("학기 선택", [1, 2])

    if st.button("다음"):
        st.session_state.grade = grade
        st.session_state.semester = semester
        st.session_state.step = 2
        st.rerun()

# Step 2: 과목 선택
elif st.session_state.step == 2:
    grade = st.session_state.grade
    semester = st.session_state.semester
    max_subjects = selection_rules[grade][semester]

    st.header(f"2️⃣ {grade}학년 {semester}학기 과목 선택")
    
    st.subheader("📌 공통과목")
    for subject in subjects[grade][semester]["공통"]: 
        st.write(f"- {subject}")

    selected_subjects = []
    if "선택" in subjects[grade][semester] and max_subjects > 0:
        st.subheader("📌 선택과목")
        st.caption(f"선택과목을 정확히 {max_subjects}개 선택해주세요.")
        selected_subjects = st.multiselect("선택과목 선택", subjects[grade][semester]["선택"])

    if st.button("다음"):
        if len(selected_subjects) != max_subjects:
            st.warning(f"선택과목을 정확히 {max_subjects}개 선택해주세요.")
        else:
            st.session_state.selected_subjects = selected_subjects
            # grade_df 초기화 제거 (step 3 진입 시 생성하도록)
            if "grade_df" in st.session_state:
                del st.session_state.grade_df
            st.session_state.step = 3
            st.rerun()

# Step 3: 성적 입력
elif st.session_state.step == 3:
    grade = st.session_state.grade
    semester = st.session_state.semester
    selected_subjects = st.session_state.selected_subjects
    
    all_subjects = (subjects[grade][semester]["공통"] + selected_subjects)
    st.header("3️⃣ 과목별 성적 입력")

    if "grade_df" not in st.session_state:
        st.session_state.grade_df = pd.DataFrame(
            {
                "과목": all_subjects,
                "수강자수": [100] * len(all_subjects),
                "등수": [10] * len(all_subjects)
            }
        )

    edited_df = st.data_editor(
        st.session_state.grade_df,
        use_container_width=True,
        key="grade_editor"
    )    

    if st.button("등급 계산"):
        if (edited_df["수강자수"] <= 0).any():
            st.error("수강자수는 1명 이상이어야 합니다.")
        elif (edited_df["등수"] <= 0).any():
            st.error("등수를 바르게 입력하세요.")
        elif (edited_df["등수"] > edited_df["수강자수"]).any():
            st.error("등수가 수강자수보다 클 수 없습니다.")
        else:
            st.session_state.grade_df = edited_df
            st.session_state.step = 4
            st.rerun()

# Step 4: 등급 계산 결과
elif st.session_state.step == 4:
    st.header("📊 등급 계산 결과")
    df = st.session_state.grade_df.copy()

    df["9등급"] = df.apply(lambda row: grade9(row["등수"], row["수강자수"]), axis=1)
    df["5등급"] = df.apply(lambda row: grade5(row["등수"], row["수강자수"]), axis=1)

    st.dataframe(df, use_container_width=True)

    avg9 = round(df["9등급"].mean(), 2)
    avg5 = round(df["5등급"].mean(), 2)

    col1, col2 = st.columns(2)
    col1.metric("9등급 시스템 평균", f"{avg9} 등급")
    col2.metric("5등급 시스템 평균", f"{avg5} 등급")

    st.session_state.target_avg_5 = st.number_input(
        "🎯 목표 5등급 평균 설정",
        min_value=1.0,
        max_value=5.0,
        value=min(2.0, float(avg5)),
        step=0.1
    )

    st.session_state.df = df

    if st.button("목표 달성 분석 보기"):
        st.session_state.step = 5
        st.rerun()

# Step 5: 목표 성적 시뮬레이션
elif st.session_state.step == 5:
    st.header("🎯 목표 성적 분석")
    df = st.session_state.df.copy()
    target_avg = st.session_state.target_avg_5

    current_avg = df["5등급"].mean()

    st.write(f"현재 5등급 평균: **{current_avg:.2f}** | 목표 5등급 평균: **{target_avg:.2f}**")

    current_grades = df["5등급"].astype(int).tolist()
    possible_grades = [list(range(1, g + 1)) for g in current_grades]

    total_combinations = math.prod(len(g) for g in possible_grades)

    progress_bar = st.progress(0)
    status_text = st.empty()

    combinations = itertools.product(*possible_grades)
    best_combination = None
    best_total_change = float("inf")

    for count, combination in enumerate(combinations, start=1):
        if count % 100 == 0 or count == total_combinations:
            progress_bar.progress(count / total_combinations)

        if sum(combination) / len(combination) <= target_avg:
            total_change = 0
            for i, target_grade in enumerate(combination):
                current_grade = current_grades[i]
                if target_grade < current_grade:
                    change = required_rank_change(df.iloc[i], target_grade)
                    total_change += change

            if total_change < best_total_change:
                best_total_change = total_change
                best_combination = combination

    progress_bar.progress(1.0)
    status_text.success("✅ 시뮬레이션 분석 완료!")

    if best_combination is not None:
        result_df = df.copy()
        result_df["목표등급"] = list(best_combination)
        result_df["목표등수"] = result_df.apply(
            lambda row: find_rank_for_grade(int(row["수강자수"]), int(row["목표등급"])), 
            axis=1
        )
        result_df["필요한 등수 상승"] = (result_df["등수"] - result_df["목표등수"]).clip(lower=0)

        st.subheader("📊 최적의 목표 등급 조합")
        st.dataframe(
            result_df[["과목", "등수", "수강자수", "5등급", "목표등급", "목표등수", "필요한 등수 상승"]],
            use_container_width=True
        )

        st.info(f"💡 목표 평균 **{target_avg:.2f}** 이하를 달성하려면 최적 조합 기준으로 **총 약 {best_total_change}등**의 상승이 필요합니다.")
    else:
        st.error("현재 성적에서 설정한 목표 평균을 달성할 수 있는 등급 조합을 찾지 못했습니다. (목표를 조금 더 완화해 보세요.)")

    if st.button("처음으로 돌아가기"):
        st.session_state.step = 0
        st.rerun()

# Step 10: 생기부 분석 난이도 선택
elif st.session_state.step == 10:
    st.header("📚 생기부 분석 스타일 선택")

    level1, level2 = st.columns(2)

    with level1:
        if st.button("🔥 매운맛 분석 (츤데레 입학사정관)", use_container_width=True):
            st.session_state.analysis_level = "Hot"
            st.session_state.step = 11
            st.rerun()

    with level2:
        if st.button("🍃 순한맛 분석 (친절한 멘토)", use_container_width=True):
            st.session_state.analysis_level = "Normal"
            st.session_state.step = 15
            st.rerun()

# Step 11: 매운맛 분석
elif st.session_state.step == 11:
    st.header("🔥 매운맛 생기부 분석")
    st.subheader("츤데레 밸런스 컨설턴트 v1.7")
    
    희망대학 = st.text_input("🏫 희망하는 대학교를 입력하세요", key="hot_univ")
    희망학과 = st.text_input("💡 희망하는 학과를 입력하세요", key="hot_dept")
    
    학생의_활동_경험 = st.text_area(
        "📚 생기부 활동 내용을 입력하세요",
        height=250,
        placeholder="활동 내용을 상세히 적어줄수록 정확도가 높아집니다.",
        key="hot_record"
    )
    
    분석_시작 = st.button("🤖 매운맛 생기부 분석 시작")

    if 분석_시작:
        if not 희망대학 or not 희망학과 or not 학생의_활동_경험.strip():
            st.warning("⚠️ 대학교, 학과, 생기부 활동을 모두 입력해주세요.")
        else:
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            except Exception as e:
                st.error("❌ API 키를 확인해주세요. Streamlit Secrets에 GEMINI_API_KEY가 설정되어 있어야 합니다.")
                st.stop()

            prompt = f"""
            너는 대한민국 최고의 대입 수시 학종(학생부종합전형) 전문 입학사정관이자, 학생을 진심으로 합격시키고 싶은 츤데레 멘토야. 나쁜 소재를 무작정 훌륭하다고 거짓말하는 '영혼 없는 칭찬'은 하지 마. 대신 "이 부분은 아쉽지만, 이렇게 바꾸면 대박이 난다"처럼 뼈 때리는 조언과 확실한 해결책(당근과 채찍)을 동시에 줘.
                
            [학생 정보]
            - 희망 대학: {희망대학}
            - 희망 학과: {희망학과}
            - 학생의 활동 기록:
            {학생의_활동_경험}
                
            다음 4가지 섹션에 맞춰 마크다운(Markdown) 문법으로 깔끔하고 흥미진진하게 리포트를 작성해줘:
                
            ### 1. 👀 {희망대학} 입학사정관의 시선 (첫인상 및 평가)
            - 학생이 입력한 활동들이 해당 대학/학과 기준에서 '평범한 수준'인지 '눈에 띄는 수준'인지 솔직한 첫인상을 적어줘.
            - 칭찬할 만한 팩트와 다소 아쉬운 한계점을 50:50 비율로 균형 있게 짚어줘.
                
            ### 2. ⚡ 팩트 폭행과 심화 돌파구 (약점 보완책)
            - 현재 활동에서 탐구의 깊이나 구체성이 부족한 허점을 날카롭게 지적해줘.
            - 하지만 거기서 끝내지 말고, 입학사정관의 마음을 완전히 돌려놓을 수 있는 '후속 심화 탐구 주제 1가지(구체적인 도서나 이론 포함)'를 무조건 제시해줘.
                
            ### 3. 💪 생기부에 꼭 박아야 할 이 활동의 '진짜 가치'
            - 이 활동이 생기부에 등재될 때, 선생님께 어필해야 할 핵심 가치 키워드 2가지를 뽑아주고 어떻게 강조해야 할지 행동 지침을 알려줘.

            ### 4. 📝 학종 합격률을 높이는 세특 문구 추천 (선생님 참고용)
            - 학생의 아쉬운 점을 완벽하게 보완하여, 고등학교 선생님이 생기부 '세부능력 및 특기사항'에 매력적으로 적어주실 수 있는 완성도 높은 문장(한 문단, 300자 내외)을 작성해줘.
            """

            st.info("🕵️ AI 입학사정관이 채찍과 당근을 들고 생기부를 분석하고 있습니다...")
            
            response = None
            for i in range(3):
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    break
                except Exception as e:
                    if "500" in str(e) or "ServerError" in str(e):
                        st.warning(f"⚠️ 구글 서버 응답 지연 발생 (재시도 {i+1}/3)...")
                        time.sleep(3)
                    else:
                        st.error(f"❌ 에러 발생: {e}")
                        break
            
            if response is None or not response.text:
                st.error("❌ 구글 서버가 일시적으로 응답하지 않습니다. 잠시 후 다시 시도해주세요.")
            else:
                분석_결과 = response.text
                st.subheader("📊 생기부 밸런스 리포트")
                st.markdown(분석_결과)
                
                파일명 = f"result_{희망대학}_{희망학과}.txt"
                try:
                    with open(파일명, "w", encoding="utf-8") as f:
                        f.write(분석_결과)
                    st.success(f"💾 분석 결과가 '{파일명}'으로 저장되었습니다.")
                except Exception as e:
                    st.info("💡 결과를 확인하셨습니다.")

# Step 15: 순한맛 분석
elif st.session_state.step == 15:
    st.header("🍃 순한맛 생기부 분석")
    st.subheader("친절한 합격 멘토 v1.7")

    희망대학 = st.text_input("🏫 희망하는 대학교를 입력하세요", key="mild_univ")
    희망학과 = st.text_input("💡 희망하는 학과를 입력하세요", key="mild_dept")
    
    학생의_활동_경험 = st.text_area(
        "📚 입학사정관이 주목할 만한 활동을 입력하세요",
        height=250,
        placeholder="생기부 활동을 여러 줄로 입력해주세요.",
        key="mild_record"
    )

    분석_시작 = st.button("🤖 순한맛 생기부 분석 시작")

    if 분석_시작:
        if not 희망대학 or not 희망학과 or not 학생의_활동_경험.strip():
            st.warning("⚠️ 대학교, 학과, 생기부 활동을 모두 입력해주세요.")
        else:
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            except Exception as e:
                st.error("❌ API 키를 확인해주세요. Streamlit Secrets에 GEMINI_API_KEY가 설정되어 있어야 합니다.")
                st.stop()

            prompt = f"""
            너는 대한민국 최고의 대입 수시 학종(학생부종합전형) 전문 입학사정관이야.
            아래 [학생 정보]를 바탕으로, 고등학교 선생님이 생기부에 기록했을 때 강력한 무기가 될 분석 리포트를 작성해줘.
        
            [학생 정보]
            - 희망 대학: {희망대학}
            - 희망 학과: {희망학과}
            - 학생의 활동 기록:
            {학생의_활동_경험}
        
            다음 가이드라인에 맞춰 마크다운(Markdown) 문법을 활용해 시각적으로 깔끔하게 출력해줘:
        
            ### 1. 🎯 {희망대학} {희망학과}가 선호하는 핵심 필수 역량
            - 해당 대학/학과에서 가장 중요하게 평가하는 역량 2가지와 그 이유를 간략히 서술해줘.
        
            ### 2. 💪 생기부 등재 시 핵심이 될 강점 (선생님께 어필할 부분)
            - 학생이 입력한 활동 중 입학사정관이 가장 흥미로워할 핵심 소재를 짚어내고, 생기부에 강조해야 할 포인트를 명시해줘.
        
            ### 3. 📉 보충해야 할 역량 및 후속 탐구 추천
            - 학종 합격을 위해 현재 활동에서 '지적 호기심'이나 '심화 탐구'가 부족한 부분을 짚어주고, 이를 보완할 수 있는 구체적인 행동(추천 독서 또는 연계 탐구 주제)을 제안해줘.
        
            ### 4. 📝 세특 예시 문구 (선생님 참고용)
            - 고등학교 선생님이 생기부 '세부능력 및 특기사항'에 그대로 참고할 수 있을 정도로 매력적인 문장(한 문단, 300자 내외)으로 작성해줘.
            """
        
            st.info("🤖 AI 입학사정관이 생기부를 분석하고 있습니다. 잠시만 기다려주세요...")
            
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                분석_결과 = response.text
                st.subheader("📊 생기부 분석 리포트")
                st.markdown(분석_결과)
            
                파일명 = f"생기부_분석_{희망대학}_{희망학과}.txt"
                try:
                    with open(파일명, "w", encoding="utf-8") as f:
                        f.write(분석_결과)
                    st.success(f"💾 분석 결과가 '{파일명}'으로 저장되었습니다.")
                except Exception as e:
                    st.info("💡 결과를 확인하셨습니다.")
            except Exception as e:
                st.error(f"❌ 분석 실패: {e}")
