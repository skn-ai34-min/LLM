import streamlit as st                               # Streamlit UI 라이브러리
from ai_wine_sommelier import ai_wine_sommelier_rag  # RAG 기반 와인 추천 체인 import

# 제목과 설명
st.title("🍷AI Wine Sommelier🍷")                     # 앱 메인 타이틀
st.write("🍖음식 이미지 URL을 작성하면, 어울리는 와인🍷을 추천해드립니다.")  # 앱 설명 문구

# 폼 생성
with st.form(key="img_form"):                              # 이미지 URL 입력용 폼
    img_url = st.text_input(
        "이미지 URL 입력:", 
        placeholder="예: https://example.com/food.jpg"
    )                                                      # 음식 이미지 URL 입력
    submit_button = st.form_submit_button(label="Submit")  # 제출 버튼

if submit_button:                                          # Submit 버튼 클릭 시
    if img_url:                                            # URL이 입력된 경우
        try:
            st.image(img_url)                              # 입력된 이미지 화면 출력

            st.subheader("AI 와인 추천:")                   # 결과 영역 제목

            # Spinner 처리
            with st.spinner("와인 검색중..."):              # 처리 중 로딩 표시
                query = {
                    'text': '',                            # 텍스트 입력 없음
                    'image_urls': [img_url]                # 이미지 URL 전달
                }
                gen_response = ai_wine_sommelier_rag(query)  # AI 소믈리에 체인 실행
                st.write_stream(gen_response)                # 스트리밍 응답 출력
        except Exception as e:
            st.error(f"이미지를 로드하는 중 오류가 발생했습니다: {e}")  # 예외 처리
    else:
        st.warning("이미지 URL을 입력해주세요!")  # URL 미입력 경고