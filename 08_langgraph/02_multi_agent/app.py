# -*- coding: utf-8 -*-
"""한글 밈 통역기 - Streamlit UI

실행: streamlit run app.py
"""
import streamlit as st

from meme_agent import (
    build_graph, image_to_data_uri, split_image_urls, NODE_LABELS, INDEX_NAME,
)

st.set_page_config(page_title='한글 밈 통역기', page_icon='🧢', layout='centered')


# ------------------------------------------------------------------ 리소스
@st.cache_resource(show_spinner='에이전트 준비중...')
def load_graph(max_retry: int):
    """그래프는 한 번만 조립 (max_retry가 바뀌면 다시 조립)"""
    return build_graph(max_retry=max_retry)


# ------------------------------------------------------------------ 사이드바
with st.sidebar:
    st.header('⚙️ 설정')

    max_retry = st.slider(
        '검색어 재작성 최대 횟수', 0, 3, 2,
        help='실패시 몇 번까지 검색어를 다시 만들지. 초과하면 웹 검색으로 넘어갑니다.'
    )
    show_trace = st.toggle('에이전트 동작 과정 보기', value=True)

    st.divider()
    st.caption(f'📦 인덱스: `{INDEX_NAME}` (503건)')
    st.caption(
        '📚 데이터: [KoCulture-Descriptions]'
        '(https://huggingface.co/datasets/huggingface-KREW/KoCulture-Descriptions)  \n'
        '원자료: 나무위키 / 트렌드어워드  \n'
        'License: CC BY-NC-SA 4.0 (비상업)'
    )

    st.divider()
    if st.button('화면 지우기', use_container_width=True):
        st.session_state.last_turn = None
        st.rerun()


# ------------------------------------------------------------------ 헤더
st.title('🧢 한글 밈 통역기')
st.caption('모르는 유행어나 짤을 물어보세요. 뜻·유래·사용법에 **지금 써도 되는지**까지 알려드립니다.')

# 직전 질문 1건만 보관한다 (대화 누적 없음)
if 'last_turn' not in st.session_state:
    st.session_state.last_turn = None


def render_images(images):
    """업로드 이미지(bytes)와 URL(str)을 함께 표시"""
    if not images:
        return
    cols = st.columns(min(len(images), 3))
    for col, img in zip(cols, images):
        col.image(img, width=200)


# ------------------------------------------------------------------ 입력
# 텍스트 / 이미지 첨부 / 이미지 URL 을 채팅창 하나로 모두 받는다
# (위젯 위치와 무관하게 화면 하단에 고정되므로 먼저 읽는다)
user_input = st.chat_input(
    '밈을 물어보거나, 짤을 첨부하거나, 이미지 URL을 붙여넣으세요',
    accept_file='multiple',
    file_type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
)
has_new_input = bool(user_input and (user_input.text or user_input.files))


# ------------------------------------------------------------------ 화면
# 새 질문이 들어오면 이전 내용은 지우고 새 것만 보여준다.
if not has_new_input:
    if st.session_state.last_turn:
        # 슬라이더/토글 조작 등으로 rerun 되어도 직전 답변은 유지
        turn = st.session_state.last_turn
        with st.chat_message('user'):
            render_images(turn.get('images'))
            st.write(turn['question'])
        with st.chat_message('assistant'):
            if turn.get('timing'):
                st.markdown(f"**타이밍** · {turn['timing']}")
            st.markdown(turn['answer'])
            if turn.get('caption'):
                st.caption(turn['caption'])
    else:
        st.info(
            '**세 가지 방법으로 물어볼 수 있어요**  \n'
            '· **텍스트** — 억텐이 무슨 뜻이야? / 중꺾마 지금 써도 돼?  \n'
            '· **짤 첨부** — 입력창의 📎 버튼으로 이미지 업로드  \n'
            '· **이미지 URL** — 짤 주소를 그대로 붙여넣기'
        )


# ------------------------------------------------------------------ 실행
if has_new_input:
    text = (user_input.text or '').strip()

    # 1) 첨부 파일 -> data URI
    image_urls = []
    display_images = []
    for f in user_input.files:
        data = f.getvalue()
        image_urls.append(image_to_data_uri(data, f.name))
        display_images.append(data)

    # 2) 텍스트에 섞인 이미지 URL 분리
    url_images, text = split_image_urls(text)
    image_urls.extend(url_images)
    display_images.extend(url_images)

    # 3) 이미지만 보냈다면 기본 질문을 채워준다
    question = text or ('이 짤 무슨 뜻이야?' if image_urls else '')

    if not question:
        st.warning('질문을 입력하거나 짤 이미지를 첨부해주세요.')
        st.stop()

    with st.chat_message('user'):
        render_images(display_images)
        st.write(question)

    graph = load_graph(max_retry)

    with st.chat_message('assistant'):
        final_state = {}

        # 노드가 실행될 때마다 진행상황 표시
        status = st.status('생각하는 중...', expanded=show_trace) if show_trace else None

        try:
            for chunk in graph.stream({
                'messages': [('human', question)],
                'image_urls': image_urls or None,
                'retry_count': 0,
            }):
                for node_name, update in chunk.items():
                    final_state.update(update)

                    if not show_trace:
                        continue

                    label = NODE_LABELS.get(node_name, node_name)

                    # 노드별로 의미있는 정보만 골라서 보여준다
                    if node_name == 'analyze_input':
                        detail = f"검색어: `{update.get('query', '')[:80]}`"
                    elif node_name == 'retrieve_meme':
                        title = update.get('meme_title') or '결과 없음'
                        date = update.get('meme_date') or '날짜없음'
                        detail = f'후보: **{title}** ({date})'
                    elif node_name == 'rewrite_query':
                        detail = (f"재작성 → `{update.get('query')}` "
                                  f"(retry {update.get('retry_count')})")
                    elif node_name == 'web_search':
                        detail = '아카이브에 없음 → 웹 검색'
                    elif node_name == 'check_timing':
                        detail = update.get('timing', '')
                    else:
                        detail = '완료'

                    status.write(f'**{label}** — {detail}')

            if status:
                status.update(label='완료', state='complete', expanded=False)

            answer = final_state['messages'][-1].content
            timing = final_state.get('timing')
            layer = final_state.get('source_layer')

            # 타이밍 배지
            if timing:
                st.markdown(f'**타이밍** · {timing}')

            st.markdown(answer)

            # 출처 표기
            caption = ''
            if layer == 'local':
                caption = '📚 출처: 로컬 밈 아카이브'
            elif layer == 'web':
                caption = '🌐 출처: 웹 검색 (아카이브에 없는 밈)'
            if caption:
                st.caption(caption)

            # 직전 1건만 보관 (이전 질문은 덮어써서 사라진다)
            st.session_state.last_turn = {
                'question': question,
                'answer': answer,
                'timing': timing,
                'images': display_images,
                'caption': caption,
            }

        except Exception as e:
            if status:
                status.update(label='오류', state='error')
            st.error(f'처리 중 오류가 발생했습니다: {e}')
