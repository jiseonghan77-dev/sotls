import streamlit as st
import pandas as pd
import itertools
import math
import time
from google import genai
from google.colab import userdata
import os

st.title("너 이 생기부로 어디갈래?")

subjects = { #과목 목록
        1: {
            1: {
                "공통": ["공통국어1", "공통수학1", "공통영어1", "통합사회1", "통합과학1", "한국사1"]
               },

            2: {
                "공통": ["공통국어2", "공통수학2", "공통영어2", "통합사회2", "통합과학2", "한국사2"]
               }
            },
        2: {
            1: {
                "공통": ["문학", "대수", "영어1", "중국어"],
             
                "선택": ["물리학", "화학", "생명과학", "지구과학"
                       ,"세계시민과 지리", "세계사", "사회와 문화", "현대사회와 윤리"]
               },

            2: {
                "공통": ["화법과 언어", "미적분1", "영어2", "중국어 회화"],
             
                "선택": ["독서 토론과 글쓰기", "경제 수학", "기하"
                       ,"역학과 에너지", "물질과 에너지", "세포와 물질대사", "지구시스템과학"
                       ,"도시의 미래 탐구", "동아시아 역사 기행", "정치", "경제", "윤리와 사상"]
               }
           },
        3: {
            1: {
                "공통": ["독서와 작문", "확률과 통계", "영어 독해와 작문", "인공지능 기초"],

                "선택": ["주제 탐구 독서", "미적분2", "미디어 영어"
                       ,"한국지리 탐구", "법과 사회", "국제 관계의 이해", "인문학과 윤리"
                       ,"전자기와 양자", "화학 반응의 세계", "생물의 유전", "행성우주과학"]
            }

        }
}

selection_rules = {1: {1: 0, 2: 0}, 2: {1: 3, 2: 4}, 3: {1: 4}}

def grade9(rank, total):
    percent = rank / total * 100
    if percent <=4:
        return 1
    elif percent <= 11:
        return 2
    elif percent <= 23:
        return 3
    elif percent <= 40:
        return 4
    elif percent <= 60:
        return 5
    elif percent <= 77:
        return 6
    elif percent <= 89:
        return 7
    elif percent <= 96:
        return 8
    else:
        return 9
    
def grade5(rank, total):
    percent = rank / total * 100
    if percent <= 10:
        return 1
    elif percent <= 34:
        return 2
    elif percent <= 66:
        return 3
    elif percent <= 90:
        return 4
    else:
        return 5

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

if "step" not in st.session_state: 
    st.session_state.step = 0

if "analysis_type" not in st.session_state:
    st.session_state.analysis_type = None

if "analysis_level" not in st.session_state:
    st.session_state.analysis_type = None

if st.session_state == 0:
    st.title("📊 학생 성적 계산 & 생기부 분석")
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

if st.session_state.step == 1: #학년 & 학기 선택
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

if st.session_state.step == 2:
    grade = st.session_state.grade #변수 정의
    semester = st.session_state.semester
    max_subjects = selection_rules[grade][semester]

    st.header(f"{grade}학년 {semester}학기")
    st.write(f"선택 과목 수 : {max_subjects}")

    st.subheader("공통과목") #공통과목 표시
    for subject in subjects[grade][semester]["공통"]: st.write(subject)

    if "선택" in subjects[grade][semester]: #선택과목 표시
        st.subheader("선택과목")
        selected_subjects = st.multiselect("선택과목 선택", subjects[grade][semester]["선택"])
    if st.button("다음"):
        if len(selected_subjects) != max_subjects:
            st.warning(f"선택과목을 정확히 {max_subjects}개 선택해주세요.")
        else:
            st.success("선택 완료!")
            st.session_state.selected_subjects = selected_subjects
            st.session_state.step = 3
    st.rerun()

if st.session_state.step == 3:
    import pandas as pd
    grade = st.session_state.grade
    semester = st.session_state.semester
    selected_subjects = st.session_state.selected_subjects
    
    all_subjects = (subjects[grade][semester]["공통"] + selected_subjects)
    st.header("과목별 성적 입력")

    if "grade_df" not in st.session_state:
        st.session_state.grade_df = pd.DataFrame(
            {
                "과목": all_subjects,
                "수강자수": [0] * len(all_subjects),
                "등수": [0] * len(all_subjects)
            }
        )

    edited_df = st.data_editor(
        st.session_state.grade_df,
        use_container_width=True
    )    

    if st.button("등급 계산"):
        if (edited_df["수강자수"] <= 0).any():
            st.error("모든 과목의 등수를 입력하세요.")
        elif (edited_df["등수"] <= 0).any():
            st.error("모든 과목의 등수를 입력하세요.")
        else:
            st.session_state.grade_df = edited_df
            st.session_state.step = 4
            st.rerun()
    
if st.session_state.step == 4:
    st.header("등급 계산 결과")
    df = st.session_state.grade_df.copy()

    df["9등급"] = df.apply(
        lambda row: grade9(row["등수"], row["수강자수"]), axis=1
    )

    df["5등급"] = df.apply(
        lambda row: grade5(row["등수"], row["수강자수"]), axis=1
    )

    st.dataframe(df, use_container_width=True)

    avg9 = round(df["9등급"].mean(), 2)
    avg5 = round(df["5등급"].mean(), 2)

    st.subheader("전체 평균")

    st.write(f"9등급 평균 : {avg9}")
    st.write(f"5등급 평균 : {avg5}")

    st.session_state.target_avg_5 = st.number_input(
        "🎯 목표 5등급 평균",
        min_value=1.0,
        max_value=5.0,
        value=2.0,
        step=0.1
    )

    # 계산한 데이터 저장
    st.session_state.df =df

    if st.button("분석 보기"):
        st.session_state.step = 5
        st.rerun()

if st.session_state.step == 5:

    st.header("🎯 목표 성적 분석")
    df = st.session_state.df.copy()
    target_avg = st.session_state.target_avg_5

    # 현재 평균
    current_avg = df["5등급"].mean()

    st.write(f"현재 5등급 평균 : {current_avg:.2f}")
    st.write(f"목표 5등급 평균 : {target_avg:.2f}")

    # 현재 등급
    current_grades = df["5등급"].astype(int).tolist()

    # 각 과목에서 만들 수 있는 목표 등급
    possible_grades = []

    for grade in current_grades:
        grades = list(range(1, grade + 1))
        possible_grades.append(grades)

    # 전체 조합 수 계산

    total_combinations = math.prod(
        len(grades) for grades in possible_grades
    )

    # 진행률 표시

    progress_bar = st.progress(0)
    status_text = st.empty()

    # 가능한 모든 등급 조합 생성
    combinations = itertools.product(*possible_grades)

    best_combination = None
    best_total_change = float("inf")

    for count, combination in enumerate(combinations, start=1):

        # 현재 진행률
        progress = count / total_combinations

        progress_bar.progress(progress)

        status_text.write(
            f"🔍 성적 조합 분석 중... "
            f"{count:,} / {total_combinations:,}"
            f"({progress * 100:.1f}%)"
        )

        # 목표 평균을 만족하는지 확인
        if sum(combination) / len(combination) <= target_avg:

            total_change = 0

            for i, target_grade in enumerate(combination):

                current_grade = current_grades[i]

                # 현재 등급보다 높은 등급을 목표로 할 경우
                if target_grade < current_grade:

                    change = required_rank_change(df.iloc[i], target_grade)
                    total_change += change

            # 지금까지보다 등수 상승량이 적으면 교체
            if total_change < best_total_change:
                best_total_change = total_change
                best_combination = combination

        # 분석 완료
        progress_bar.progress(1.0)
        status_text.success("✅ 분석 완료!")

        # 결과 출력
        if best_combination is not None:

            result_df = df.copy()
            result_df["목표등급"] = best_combination
            result_df["목표등수"] = result_df.apply(
                lambda row: find_rank_for_grade(
                    int(row["수강자수"]),
                    int(row["목표등급"])
                ), 
                axis=1
            )

            result_df["필요한 등수 상승"] = (
                result_df["등수"] - result_df["목표등수"]
            ).clip(lower=0)

            st.subheader("📊 최적의 목표 등급 조합")

            st.dataframe(
                result_df[
                    [
                        "과목", "등수", "수강자수", "5등급", "목표등급", "목표등수", "필요한 등수 상승"
                    ]
                ],
                use_container_width=True
            )

            st.header("🎯 분석 결과")

            st.write(
                f"목표 평균 {target_avg:.2f}이하를 만들기 위해 "
                f"필요한 총 등수 상승은 약 {best_total_change}등입니다."
            )

        else:

            st.write(
                "현재 성적에서 설정한 목표 평균을 달성할 수 있는 "
                "등급 조합을 찾지 못했습니다."
            )

if st.session_state.step == 10:
    st.title("📚 생기부 분석")
    st.subheader("생기부 분석, 어떤 맛으로?")

    level1, level2 = st.columns(2)

    with level1:
        if st.button("🔥 매운맛 분석", use_container_width=True):
            st.session_state.analysis_level = "Hot"
            st.session_state.step = 11
            st.rerun()

    with level2:
        if st.button("🍃 순핫맛 분석", use_container_width=True):
            st.session_state.analysis_level = "Normal"
            st.session_state.step = 15
            st.rerun()

if st.session_state == 11:
        # 1. API 클라이언트 설정
        try:
            os.environ["GEMINI_API_KEY"] = userdata.get('GEMINI_API_KEY')
            client = genai.Client()
        except Exception as e:
            print("❌ API 키를 확인해주세요. 왼쪽 열쇠 메뉴에 GEMINI_API_KEY가 있어야 합니다.")
        
        print("=== 🎓 너 이 생기부로 어디갈래? - 츤데레 밸런스 컨설턴트 v1.7 ===")
        
        while True:
            print("\n" + "="*50)
            print("🔄 새로운 학생의 생기부 분석을 시작합니다. (종료하려면 대학 이름에 '종료' 입력)")
            print("="*50)
        
            희망대학 = input("🏫 희망하는 대학교를 입력하세요: ")
            if 희망대학.strip() == "종료":
                print("👋 프로그램을 종료합니다. 이용해 주셔서 감사합니다!")
                break
        
            희망학과 = input("💡 희망하는 학과를 입력하세요: ")
        
            print(f"\n[안내] {희망대학} {희망학과} 기준, 밸런스 있는 평가를 위한 활동을 적어주세요.")
            print("👉 입력 완료 시, 빈 칸에서 그냥 '엔터(Enter)'를 한 번 더 누르세요!\n")
        
            활동_리스트 = []
            while True:
                line = input("👉 활동 기록 입력: ")
                if not line.strip():
                    break
                활동_리스트.append(f"- {line}")
        
            if not 활동_리스트:
                print("❌ 입력된 활동이 없어 이번 분석은 취소됩니다.")
                continue
        
            학생의_활동_경험 = "\n".join(활동_리스트)
        
            # 이 부분에서 따옴표가 정확히 열리고 닫혀야 에러가 안 납니다!
            prompt = f"""
            너는 대한민국 최고의 대입 수시 학종(학생부종합전형) 전문 입학사정관이자, 학생을 진심으로 합격시키고 싶은 츤데레 멘토야.
            나쁜 소재를 무작정 훌륭하다고 거짓말하는 '영혼 없는 칭찬'은 하지 마. 대신 "이 부분은 아쉽지만, 이렇게 바꾸면 대박이 난다"처럼 뼈 때리는 조언과 확실한 해결책(당근과 채찍)을 동시에 줘.
        
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
        
            print("\n🕵️ AI 입학사정관이 채찍과 당근을 들고 생기부를 분석하고 있습니다...")
        
            # 구글 500 서버 에러 방지 로직
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
                        print(f"⚠️ 구글 서버 응답 지연 발생 (재시도 {i+1}/3)... 3초 후 다시 시도합니다.")
                        time.sleep(3)
                    else:
                        print(f"❌ 예기치 못한 에러 발생: {e}")
                        break
        
            if response is None:
                print("❌ 구글 서버가 일시적으로 먹통입니다. 잠시 후 다시 이 사람부터 실행해 주세요.")
                continue
        
            분석_결과 = response.text
        
            print("\n======================= [생기부 밸런스 리포트] =======================")
            print(분석_결과)
            print("====================================================================")
        
            # 파일 저장
            # 파일 이름에 특수문자나 공백이 들어가 오류가 나는 것을 방지하기 위해 형식을 간단히 바꿨습니다.
            파일명 = f"result_{희망대학}_{희망학과}.txt"
            with open(파일명, "w", encoding="utf-8") as f:
                f.write(분석_결과)
            print(f"\n💾 시스템: '{파일명}' 파일이 좌측 폴더 메뉴에 저장되었습니다.")
        
            time.sleep(1)

if st.session_state == 15:
    # 1. API 클라이언트 설정
        try:
            os.environ["GEMINI_API_KEY"] = userdata.get('GEMINI_API_KEY')
            client = genai.Client()
        except Exception as e:
            print("❌ API 키를 확인해주세요. 왼쪽 열쇠 메뉴에 GEMINI_API_KEY가 있어야 합니다.")
        
        print("=== 🎓 너 이 생기부로 어디갈래? - 기능 2 컨설턴트 ===")
        희망대학 = input("🏫 희망하는 대학교를 입력하세요: ")
        희망학과 = input("💡 희망하는 학과를 입력하세요: ")
        
        print(f"\n[안내] {희망대학} {희망학과} 입학사정관이 주목할 만한 활동을 한 줄씩 적어주세요.")
        print("👉 활동 입력을 모두 마치려면, 빈 칸에서 그냥 '엔터(Enter)'를 한번 더 누르세요!\n")
        
        활동_리스트 = []
        while True:
            line = input("👉 활동 기록 입력: ")
            # 아무것도 입력 안 하고 엔터만 치면 종료! (Q 입력 필요 없음)
            if not line.strip():
                break
            활동_리스트.append(f"- {line}")
        
        if not 활동_리스트:
            print("❌ 입력된 활동이 없어 프로그램을 종료합니다.")
        else:
            학생의_활동_경험 = "\n".join(활동_리스트)
        
            # 고도화 프롬프트
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
            - 학종 합격을 위해 현재 활동에서 '지적 호기심'이나 '심화 탐구'가 부족한 부분을 날카롭게 지적하고, 이를 보완할 수 있는 구체적인 행동(추천 독서 또는 연계 탐구 주제)을 제안해줘.
        
            ### 4. 📝 씹지리는 세특 예시 문구 (선생님 참고용)
            - 고등학교 선생님이 생기부 '세부능력 및 특기사항'에 그대로 붙여넣어도 손색없을 정도로 매력적인 문장(한 문단, 300자 내외)으로 작성해줘.
            """
        
            print("\n🤖 AI 입학사정관이 생기부를 매섭게 분석하고 있습니다. 잠시만 기다려주세요...\n")
        
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
        
            분석_결과 = response.text
        
            print("======================= [생기부 분석 리포트] =======================")
            print(분석_결과)
            print("====================================================================")
        
            파일명 = f"생기부_분석_{희망대학}_{희망학과}.txt"
            with open(파일명, "w", encoding="utf-8") as f:
                f.write(분석_결과)
            print(f"\n💾 시스템: '{파일명}' 파일이 좌측 폴더 메뉴에 저장되었습니다.")
