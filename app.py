import streamlit as st
import pandas as pd
import openai

st.set_page_config(page_title = "생기부용 요약 프로그램(by 리로스쿨 & ChatGPT)", layout="wide")

# --- 코드 수정 시작 ---

# 기능 구현 함수
# api_key를 함수의 인자로 받도록 수정
def askGpt(prompt, api_key):
    # 인자로 받은 api_key를 사용하여 클라이언트 초기화
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o", # 최신 모델인 gpt-4o로 변경 (o1-preview는 곧 지원 중단될 수 있음)
        messages=[{"role": "user",
                   "content": prompt}]
    )
    gptResponse = response.choices[0].message.content
    return gptResponse

def main():
    # --- 사이드바에 API 키 입력 필드 추가 ---
    st.sidebar.title("API Key 설정")
    api_key = st.sidebar.text_input("OpenAI API 키를 입력하세요.", type="password", key="api_key_input")
    st.sidebar.markdown("[API 키 발급받기](https://platform.openai.com/api-keys)")
    
    # --- 메인 화면 구성 ---
    st.title("생기부용 문장 요약 및 생성 프로그램")
    st.info("리로스쿨에서 내려받은 엑셀 파일을 업로드하면, ChatGPT를 활용하여 학생별 특기사항 초안을 생성해줍니다.")

    file = st.file_uploader("리로스쿨에서 다운 받은 엑셀 파일을 업로드하세요", type=["xlsx"])
    
    if file is not None:
        df = pd.read_excel(file)
        st.dataframe(df)
        st.write("업로드된 데이터 행/열 개수:", df.shape)
        
        # 제외할 열 인덱스 (기존 로직 유지)
        # 데이터프레임의 열 개수에 따라 동적으로 조정될 수 있도록 예외처리 추가
        try:
            exclude_indices = [0, 1, 2, 5, 7] + list(range(len(df.columns)-11, len(df.columns)))
            # 제외할 열 이름 가져오기
            exclude_columns = [df.columns[i] for i in exclude_indices if i < len(df.columns)]
            # 제외하고 새로운 DataFrame 생성
            new_df = df.drop(columns=exclude_columns)
        except IndexError:
            st.error("엑셀 파일의 열 구조가 예상과 다릅니다. 원본 파일이 맞는지 확인해주세요.")
            st.stop() # 오류 발생 시 프로그램 중단

        st.warning("순번, 아이디, 학번, 필명, 글내용(통합), 교사평가, 글번호, 투표, 득표, 1차점수, 점수, 조회, 첨부, 제출일, 최종수정일, IP등은 제외하고 다음의 열들만 남깁니다.")
        st.dataframe(new_df)

        byte = st.text_input("업로드한 파일의 바이트 수를 입력해주세요. (예: 500)", key="byte_input")

        description = st.text_input("어떤 활동에 대한 학생의 입력 자료인지 입력해주세요. (예: 'AI 윤리 원칙 탐구 보고서 작성 활동')", key="description")

        descriptions = []
        
        st.markdown("---")
        st.subheader("각 항목에 대한 설명 입력")
        st.markdown("학생들이 입력한 각 항목이 무엇을 의미하는지 구체적으로 설명해주세요. 이 설명은 AI가 학생의 활동을 이해하는 데 큰 도움이 됩니다.")

        # new_df의 2번째 열부터 시작 (일반적으로 이름, 학번 다음부터의 항목)
        for i in range(2, len(new_df.columns)):
            col_name = new_df.columns[i]
            desc = st.text_input(f"항목 '{col_name}'에 대한 설명을 입력해주세요.", key=f"desc_{i}")
            descriptions.append(desc)
        
        st.markdown("---")

        if st.button("✨ 특기사항 생성하기"):
            # --- API 키 입력 여부 확인 로직 추가 ---
            if not api_key:
                st.error("사이드바에 OpenAI API 키를 먼저 입력해주세요.")
            elif not description.strip():
                st.warning("어떤 활동에 대한 자료인지 설명을 입력해주세요.")
            else:
                with st.spinner('AI가 학생별 요약문을 생성 중입니다. 잠시만 기다려주세요...'):
                    explanation_text = "\n".join([
                        f"- {col} : {desc}" for col, desc in zip(new_df.columns[2:], descriptions) if desc.strip()
                    ])

                    # 결과를 저장할 리스트
                    results = []

                    for idx, row in new_df.iterrows():
                        student_name = row[new_df.columns[0]] # 학생 이름 또는 식별자
                        student_inputs = "\n".join([
                            f"{col} : {row[col]}" for col in new_df.columns[2:]
                        ])

                        prompt = f'''
                        **Instructions**:
                        - 당신은 고등학교 교사로서, 학생이 동아리 활동에서 작성한 보고서 내용을 바탕으로 학생의 역량과 특성을 평가하여 학교생활기록부 특기사항을 기록하는 전문가입니다.
                        - 학생의 보고서 내용을 그대로 복사하지 말고, 내용을 근거로 교사의 관찰자적 시점에서 학생의 행동 특성, 역량, 잠재력 등을 서술해야 합니다.
                        - 문장의 종결어미는 '~함', '~음', '~임'과 같은 개조식으로 명료하게 작성해주세요.
                        - 받침이 있는 한글은 3byte, 받침이 없는 한글은 2byte, 공백 및 영어는 2byte입니다. 전체 내용은 {byte} 내외로 요약해주세요.

                        **활동 개요**: {description}

                        **보고서 항목별 설명**:
                        {explanation_text}

                        **학생이 제출한 보고서 내용**:
                        {student_inputs}

                        위 내용을 바탕으로, 교사의 관찰자 입장에서 학교생활기록부에 기재할 특기사항을 작성해주세요.
                        '''
                        
                        # 수정된 askGpt 함수 호출 (api_key 전달)
                        try:
                            context = askGpt(prompt, api_key)
                            st.markdown(f"### {row[new_df.columns[0]]} 학생 요약 결과 ({idx+1}/{len(new_df)})")
                            st.success(context)
                            results.append({'학생': student_name, '생성된 특기사항': context})
                        except openai.AuthenticationError:
                            st.error("입력하신 OpenAI API 키가 유효하지 않습니다. 확인 후 다시 시도해주세요.")
                            st.stop()
                        except Exception as e:
                            st.error(f"오류가 발생했습니다: {e}")
                            st.stop()
                    
                    # 모든 학생 처리 후 다운로드 버튼 제공
                    st.markdown("---")
                    st.header("전체 결과 다운로드")
                    result_df = pd.DataFrame(results)
                    csv = result_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="CSV 파일로 결과 다운로드하기",
                        data=csv,
                        file_name=f'{description}_특기사항_요약결과.csv',
                        mime='text/csv',
                    )

# --- 코드 수정 끝 ---

if __name__ == "__main__":
    main()