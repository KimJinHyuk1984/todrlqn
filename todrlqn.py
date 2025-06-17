import streamlit as st
import pandas as pd
import openai

st.set_page_config(page_title = "생기부용 요약 프로그램(by 리로스쿨 & ChatGPT)", layout="wide")

# 기능 구현 함수 
def askGpt(prompt):
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user",
                  "content": prompt}]
    )
    gptResponse = response.choices[0].message.content
    return gptResponse

def main():
    file = st.file_uploader("리로스쿨에서 다운 받은 엑셀 파일을 업로드하세요", type=["xlsx"])
    if file is not None:
        df = pd.read_excel(file)
        st.dataframe(df)
        st.write(df.shape)
        # 제외할 열 인덱스
        exclude_indices = [0, 1, 2, 5, 7] + list(range(len(df.columns)-11, len(df.columns)))

        # 제외할 열 이름 가져오기
        exclude_columns = [df.columns[i] for i in exclude_indices]

        # 제외하고 새로운 DataFrame 생성
        new_df = df.drop(columns=exclude_columns)

        #st.write("원본 데이터프레임:", df.shape)
        #st.write("제외 후 데이터프레임:", new_df.shape)
        st.warning("순번, 아이디, 학번, 필명, 글내용(통합), 교사평가, 글번호, 투표, 득표, 1차점수, 점수, 조회, 첨부, 제출일, 최종수정일, IP등은 제외하고 다음의 열들만 남깁니다.")
        st.dataframe(new_df)

        description = st.text_input("어떤 활동에 대한 학생의 입력 자료인지 입력해주세요.", key="description")

        descriptions = []

        for i in range(2, len(new_df.columns)):
            col_name = new_df.columns[i]
            desc = st.text_input(f"{col_name}에 대한 설명을 입력해주세요.", key=f"desc_{i}")
            descriptions.append(desc)
        st.write("입력된 설명들:", descriptions)

        if st.button("요약"):
            explanation_text = "\n".join([
                f"- {col} : {desc}" for col, desc in zip(new_df.columns[2:], descriptions)
            ])

            for idx, row in new_df.iterrows():
                # 학생 입력 데이터를 하나의 문자열로 구성
                student_inputs = "\n".join([
                    f"{col} : {row[col]}" for col in new_df.columns[2:]
                ])

                prompt = f'''
                **Instructions**:
                - 당신은 학생이 동아리 활동을 통해 작성한 보고서의 내용을 바탕으로 학생을 평가하여 특기사항을 기록하는 전문가입니다.
                - 당신이 작성한 글에는 다음의 내용을 포함해야 합니다.
                - 학생이 작성한 글을 그대로 가져오지 말고 학생의 글을 통해 교사가 관찰하는 입장에서 작성합니다.
                - 문장의 종결어미는 '임', '함' 등의 개조식 형태로 작성합니다.
                - 학생들이 참여한 활동에 대한 설명은 다음과 같습니다 : {description}

                📌 각 열에 대한 설명:
                {explanation_text}

                📎 학생 입력 내용:
                {student_inputs}

                위 내용을 바탕으로 관찰자의 입장에서 특기사항을 작성해주세요.
                '''

                context = askGpt(prompt)
                st.markdown(f"### {idx+1}번 학생 요약 결과")
                st.success(context)

if __name__ == "__main__":
    main()
                    
