# -*- coding: utf-8 -*-
"""한글 밈 통역기 - 에이전트 로직

agent.ipynb의 그래프를 Streamlit에서 재사용하기 위해 모듈로 분리한 것.
노트북과 달리 print() 대신 graph.stream()으로 진행상황을 UI에 넘긴다.
"""
from dotenv import load_dotenv
import os
import re
import base64
import mimetypes
import requests
from datetime import datetime
from urllib.parse import urlparse
from typing import List, Optional, Literal, TypedDict, Annotated, Tuple

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

load_dotenv()

INDEX_NAME = 'korean-meme'
MODEL_NAME = 'gpt-5.4-mini'

# 노드 이름 -> UI 표시용 한글 라벨
NODE_LABELS = {
    'analyze_input': '입력 분석',
    'retrieve_meme': '아카이브 검색',
    'rewrite_query': '검색어 재작성',
    'web_search': '웹 검색 폴백',
    'check_timing': '타이밍 판정',
    'generate_answer': '답변 생성',
}


# ---------------------------------------------------------------- State
class MemeState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    image_urls: Optional[List[str]]
    query: Optional[str]
    context: Optional[str]
    meme_title: Optional[str]
    meme_date: Optional[str]
    timing: Optional[str]
    retry_count: int
    source_layer: Optional[str]


# ---------------------------------------------------------------- 유틸
def image_to_data_uri(data: bytes, filename: str = 'image.jpg') -> str:
    """업로드된 이미지 바이트를 base64 data URI로 변환"""
    mime = mimetypes.guess_type(filename)[0] or 'image/jpeg'
    b64 = base64.b64encode(data).decode()
    return f'data:{mime};base64,{b64}'


URL_PATTERN = re.compile(r'https?://[^\s<>"\']+')
IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')


def is_image_url(url: str) -> bool:
    """URL이 이미지를 가리키는지 판별"""
    # 1차: 확장자로 판단
    if urlparse(url).path.lower().endswith(IMAGE_EXTS):
        return True
    # 2차: 확장자가 없으면 Content-Type 확인 (네이버 등 쿼리스트링 형태 URL 대응)
    try:
        res = requests.head(url, timeout=3, allow_redirects=True)
        return res.headers.get('content-type', '').startswith('image/')
    except Exception:
        return False


def split_image_urls(text: str) -> Tuple[List[str], str]:
    """채팅 텍스트에서 이미지 URL을 분리해낸다.

    Returns:
        (이미지 URL 목록, URL이 제거된 나머지 텍스트)
    """
    if not text:
        return [], ''

    image_urls = []
    cleaned = text

    for url in URL_PATTERN.findall(text):
        if is_image_url(url):
            image_urls.append(url)
            cleaned = cleaned.replace(url, ' ')

    return image_urls, ' '.join(cleaned.split())


# ---------------------------------------------------------------- 프롬프트
VISION_PROMPT = """
당신은 이미지에 있는 정보를 그대로 옮겨적는 기록자입니다.

[반드시 지킬 것]
1. 이미지에 적힌 한글/영어 텍스트를 **오탈자까지 그대로** 옮겨 적으세요.
2. 등장인물의 표정, 행동, 복장, 배경을 **객관적으로** 묘사하세요.
3. 알아볼 수 있는 인물/캐릭터/프로그램이 있다면 이름을 적으세요.

[절대 하지 말 것]
- 밈의 의미나 뜻을 추측하지 마세요.
- 유래를 지어내지 마세요.
- "~인 것 같다", "~를 의미한다" 같은 해석을 하지 마세요.

[출력 형식]
자막: (이미지 속 텍스트 그대로)
장면: (객관적 묘사 2~3문장)
"""

GRADE_PROMPT = (
    "당신은 검색된 밈 설명이 사용자의 질문에 답할 수 있는지 판단하는 평가자입니다.\n\n"
    "검색된 밈 설명:\n{context}\n\n"
    "사용자 입력:\n{question}\n\n"
    "사용자가 궁금해하는 그 밈/표현이 검색 결과에 실제로 포함되어 있으면 'yes',\n"
    "전혀 다른 밈이 검색되었거나 관련이 없으면 'no'로 답하세요.\n"
    "단순히 주제가 비슷한 정도라면 'no'입니다."
)

REWRITE_PROMPT = """
아래 입력에서 **밈/유행어로 보이는 핵심 표현만** 뽑아 검색어로 만드세요.

[규칙]
- 설명 문장이 아니라 검색 키워드로 만드세요.
- 조사, 존댓말, 물음표는 제거하세요.
- 짤 서술이라면 자막에 있는 표현을 우선하세요.
- 검색어만 출력하고 다른 말은 하지 마세요.

[이전 검색어]
{query}

[예시]
"아들이 카톡에 어쩔티비라고 보냈는데 무슨 뜻이야?" -> 어쩔티비
"자막: 갑자기 분위기 싸해짐 / 장면: 남성이 정색하는 표정" -> 갑분싸
"""

ANSWER_PROMPT = """
당신은 인터넷 밈을 모르는 사람에게 친절하게 설명해주는 '밈 통역사'입니다.
아래 자료만 근거로 사용해 답변하세요. 자료에 없는 내용은 지어내지 마세요.

## 검색된 자료 ##
{context}

## 타이밍 판정 ##
{timing}

## 사용자 입력 ##
{query}

## 답변 형식 ##
**뜻**: 한 문장으로 간단명료하게

**유래**: 어디서 시작됐는지 2~3문장

**이렇게 씁니다**: 실제 사용 예시 1~2개

**지금 써도 될까?**: 위 타이밍 판정을 자연스러운 문장으로 풀어서 설명

**주의**: 쓰면 안 되는 상황이 있다면 알려주기 (회사, 윗사람 앞 등). 없으면 생략.

자료가 사용자 질문과 명백히 무관하다면, 솔직하게 "찾지 못했다"고 답하세요.
"""


class GradeDocuments(BaseModel):
    binary_score: str = Field(description="관련이 있으면 'yes', 없으면 'no'")


# ---------------------------------------------------------------- 리소스
def get_vector_store():
    embeddings = OpenAIEmbeddings(model='text-embedding-3-small')
    return PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)


# ---------------------------------------------------------------- 그래프
def build_graph(max_retry: int = 2):
    """밈 통역기 그래프를 조립해 반환"""

    llm = init_chat_model(MODEL_NAME, temperature=0)
    grader_model = init_chat_model(MODEL_NAME, temperature=0)
    vector_store = get_vector_store()
    tavily_tool = TavilySearch(max_results=3)

    # ---------------- 노드 ----------------
    def analyze_input(state: MemeState):
        """이미지가 있으면 Vision으로 서술, 없으면 질문을 그대로 검색 쿼리로"""
        image_urls = state.get('image_urls')
        user_text = state['messages'][-1].content

        if image_urls:
            content = [{'type': 'text', 'text': VISION_PROMPT}]
            for url in image_urls:
                content.append({'type': 'image_url', 'image_url': {'url': url}})
            description = llm.invoke([HumanMessage(content=content)]).content
            query = f'{description}\n{user_text}'.strip()
        else:
            query = user_text

        return {'query': query, 'retry_count': 0}

    def retrieve_meme(state: MemeState):
        """벡터DB에서 밈 후보를 검색하고 메타데이터를 State에 저장"""
        docs = vector_store.similarity_search(state['query'], k=3)

        if not docs:
            return {'context': '', 'source_layer': 'local'}

        top = docs[0]
        return {
            'context': '\n\n'.join(doc.page_content for doc in docs),
            'meme_title': top.metadata.get('title'),
            'meme_date': top.metadata.get('date'),
            'source_layer': 'local',
        }

    def grade_documents(state: MemeState) -> Literal['check_timing', 'rewrite_query', 'web_search']:
        """검색 결과의 관련성을 채점하여 다음 노드를 결정 (조건부 엣지)"""
        if not state.get('context'):
            return 'web_search'

        prompt = PromptTemplate.from_template(GRADE_PROMPT)
        chain = prompt | grader_model.with_structured_output(GradeDocuments)
        response = chain.invoke({'question': state['query'], 'context': state['context']})

        score = response.binary_score.strip().lower()
        retry = state.get('retry_count', 0)

        if score == 'yes':
            return 'check_timing'
        if retry < max_retry:
            return 'rewrite_query'
        return 'web_search'

    def rewrite_query(state: MemeState):
        """검색 실패시 쿼리를 키워드 중심으로 재작성"""
        prompt = PromptTemplate.from_template(REWRITE_PROMPT)
        chain = prompt | llm
        new_query = chain.invoke({'query': state['query']}).content.strip()
        return {'query': new_query, 'retry_count': state.get('retry_count', 0) + 1}

    def web_search(state: MemeState):
        """아카이브에서 못 찾았을 때 웹에서 검색"""
        result = tavily_tool.invoke({'query': f"{state['query']} 밈 뜻 유래"})

        docs = []
        for r in result.get('results', []):
            docs.append(f"[{r.get('title')}]\n{r.get('content')}\n출처: {r.get('url')}")

        return {
            'context': '\n\n'.join(docs),
            'source_layer': 'web',
            'meme_date': '',
            'timing': '시기 정보 없음 (웹 검색 결과)',
        }

    def check_timing(state: MemeState):
        """밈의 등장 시기와 현재를 비교해 신선도를 판정 (LLM 호출 없음)"""
        date_str = (state.get('meme_date') or '').strip()

        if not date_str:
            timing = '❓ 시기 불명 - 데이터에 등장 시점이 기록되어 있지 않음'
        else:
            year = int(date_str[:4])
            years_ago = datetime.now().year - year
            if years_ago <= 1:
                timing = f'🔥 현재 진행형 ({year}년 등장) - 지금 써도 자연스러움'
            elif years_ago <= 3:
                timing = f'😐 살짝 지남 ({year}년 등장, {years_ago}년 경과) - 다들 알아듣지만 새롭진 않음'
            else:
                timing = f'🦕 올드함 ({year}년 등장, {years_ago}년 경과) - 지금 쓰면 옛날 사람 취급받을 수 있음'

        return {'timing': timing}

    def generate_answer(state: MemeState):
        """검색 결과 + 타이밍 판정을 종합해 최종 답변 생성"""
        prompt = PromptTemplate.from_template(ANSWER_PROMPT)
        chain = prompt | llm

        response = chain.invoke({
            'context': state.get('context') or '(검색 결과 없음)',
            'timing': state.get('timing') or '시기 정보 없음',
            'query': state['query'],
        })
        return {'messages': [response]}

    # ---------------- 그래프 ----------------
    builder = StateGraph(MemeState)

    builder.add_node('analyze_input', analyze_input)
    builder.add_node('retrieve_meme', retrieve_meme)
    builder.add_node('rewrite_query', rewrite_query)
    builder.add_node('web_search', web_search)
    builder.add_node('check_timing', check_timing)
    builder.add_node('generate_answer', generate_answer)

    builder.add_edge(START, 'analyze_input')
    builder.add_edge('analyze_input', 'retrieve_meme')
    builder.add_conditional_edges('retrieve_meme', grade_documents, {
        'check_timing': 'check_timing',
        'rewrite_query': 'rewrite_query',
        'web_search': 'web_search',
    })
    builder.add_edge('rewrite_query', 'retrieve_meme')
    builder.add_edge('web_search', 'generate_answer')
    builder.add_edge('check_timing', 'generate_answer')
    builder.add_edge('generate_answer', END)

    return builder.compile()
