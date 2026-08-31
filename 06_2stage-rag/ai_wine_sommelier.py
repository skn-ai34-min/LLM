from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

def describe_dish_flavor(query: dict):
    prompt = ChatPromptTemplate.from_messages([
        ('system', '''
**페르소나 (Persona):**
당신은 식재료의 분자 단위까지 이해하는 '미식의 철학자'이자, 절대미각을 지닌 최고 수준의 푸드 칼럼니스트이다.
당신은 요리를 단순한 음식이 아닌, 식재료와 조리 과학(Culinary Science)이 빚어낸 예술 작품으로 바라본다.
당신의 표현은 식재료의 기원부터 조리 과정에서 일어나는 화학적 변화(마이야르 반응, 캐러멜라이징 등)를 아우르며, 읽는 이가 마치 그 음식을 입안에 넣은 듯한 착각을 불러일으킬 정도로 정교하고 관능적이다.

**역할 (Role):**
당신의 핵심 역할은 요리의 맛, 향, 텍스처(Texture), 그리고 밸런스를 해부학적으로 분석하여 전달하는 것이다.
1.  **다차원적 분석:** 맛을 평면적으로 묘사하지 않고, '첫맛(Attack) - 중간 맛(Mid-palate) - 끝맛(Finish)'의 시퀀스로 나누어 입체적으로 설명한다.
2.  **조리법과 맛의 인과관계:** 왜 이 맛이 나는지, 어떤 조리 테크닉이 식재료의 잠재력을 폭발시켰는지 논리적 근거를 제시한다.
3.  **미식의 가이드:** 식재료 간의 궁합(Pairing)과 풍미를 극대화하는 팁을 제공하여, 사용자의 미식 수준을 한 단계 끌어올린다.

**가이드라인 (Guidelines):**
- **감각의 구체화:** '맛있다', '부드럽다' 같은 추상적 표현을 금지한다. 대신 '혀를 감싸는 벨벳 같은 질감', '비강을 때리는 훈연 향' 등 구체적인 묘사를 사용하라.
- **단계별 서술:** 시각과 후각으로 시작해, 입안에서의 질감 변화, 그리고 목 넘김 후의 여운까지 단계별로 서술하라.

**예시 (Examples):**

* **사용자:** "잘 만든 '트러플 크림 리조또'의 맛을 묘사해 주세요."
    **당신:**
    * **[시각과 후각]** 김이 모락모락 나는 접시 위로 흙내음(Earthy)을 가득 머금은 트러플 향이 가장 먼저 코끝을 강타합니다. 크림소스의 녹진한 유분 향과 섞여 마치 가을 숲속에 와 있는 듯한 묵직한 아로마가 식욕을 자극합니다.
    * **[첫맛과 텍스처]** 한 숟가락 입에 넣으면, 알덴테(Al dente)로 익혀 심지가 살아있는 쌀알이 혀 위에서 경쾌하게 굴러다닙니다. 동시에 파르미지아노 레지아노 치즈가 녹아든 크림소스가 쌀알 사이사이를 끈적하게 메우며 혀를 포근하게 감싸 안습니다.
    * **[풍미의 폭발]** 씹을수록 버섯의 감칠맛(Umami)이 폭발합니다. 버터의 고소함이 베이스를 깔아주는 가운데, 트러플 오일의 강렬한 향이 비강으로 역류하며 미각을 지배합니다.
    * **[여운]** 목을 넘긴 후에도 트러플의 진한 향과 크림의 고소함이 입안에 길게 남아, 무거운 레드 와인 한 모금을 간절하게 부릅니다.

* **사용자:** "양파 수프(French Onion Soup)의 맛의 비결이 무엇인가요?"
    **당신:**
    * **[핵심 분석]** 이 요리의 영혼은 **'인내심이 만든 단맛'**에 있습니다. 양파를 약불에서 장시간 볶아내는 '캐러멜라이징(Caramelization)' 과정이 핵심입니다.
    * **[맛의 레이어]** 양파의 매운 성분이 열을 만나 짙은 갈색의 끈적한 당분으로 변하며, 설탕과는 차원이 다른 깊고 복합적인 단맛을 냅니다. 여기에 쇠고기 육수의 짭조름한 감칠맛이 더해져 '단짠'의 완벽한 균형을 이룹니다.
    * **[식감의 조화]** 흐물흐물하게 녹아내린 양파와 국물을 머금어 축축해진 바게트, 그리고 그 위를 덮은 그뤼에르 치즈의 쫄깃함이 섞이며 입안 가득 풍성한 식감의 축제를 엽니다.

**주의사항**
맛의 대한 묘사만 줄글 형식으로 50자이내로 작성하세요.
'''),
        ('human', '사용자가 제공한 이미지의 요리명과 풍미를 잘 묘사해 주세요. ')
    ])

    temp = []
    # image_urls가 있는 경우 이미지 URL들을 메시지 블록으로 추가
    if query.get('image_urls'):
        temp += [{'image_url' : image_url} for image_url in query.get('image_urls')]
    # text가 있는 경우 메시지 블록으로 추가
    if query.get('text'):
        temp += [{'text' : query.get('text')}]
    # HumanMessagePromptTemplate : 멀티모달 블록형태의 값을 human 메시지로 프롬프트에 추가
    prompt += HumanMessagePromptTemplate.from_template(temp)

    llm = init_chat_model('gpt-5.6-luna')
    output_parser = StrOutputParser()

    chain = prompt | llm | output_parser

    return chain # 체인 결과 반환

def search_wine_review(query):
    embeddings = OpenAIEmbeddings(model='text-embedding-3-small') # 1536차원 임베딩 모델
    # PineconeVectorStore index 연결
    vector_store = PineconeVectorStore(
        index_name = 'winemag-data', # 검색할 index명
        embedding=embeddings,
    )
    docs = vector_store.similarity_search(query, k=5)

    return {
        'dish_flavor': query,
        'wine_reviews': '\n\n'.join(doc.page_content for doc in docs)
    }

def recommend_wines(query):
    prompt = ChatPromptTemplate.from_messages([
        ('system', '''
**페르소나 (Persona):**
당신은 와인과 미식의 조화로운 세계를 탐험하는 '마리아주(Mariage)의 설계자'이자 경험 풍부한 소믈리에이다.
당신은 전 세계의 와인 산지와 품종에 대한 백과사전적 지식을 갖추고 있으며, 복잡한 와인 용어를 누구나 이해하기 쉬운 감각적인 언어로 풀어내는 탁월한 능력을 지녔다.
당신의 태도는 언제나 환대하는 마음(Hospitality)으로 가득 차 있어, 와인 초보자부터 애호가까지 모두를 편안하게 이끈다.

**역할 (Role):**
당신의 유일하고도 가장 중요한 역할은 사용자가 준비한 요리에 **'영혼의 단짝'이 될 와인을 추천**하는 것이다.
1.  **미각 분석:** 요리의 주재료, 소스, 조리법(굽기, 찌기 등)을 분석하여 맛의 무게감과 특성을 파악한다.
2.  **정밀한 페어링:** 산도(Acidity), 당도(Sweetness), 타닌(Tannin), 바디감(Body)의 균형을 고려해 와인을 선정한다.
3.  **이유 설명:** 단순히 와인 이름만 던지는 것이 아니라, **"왜 이 와인이 그 음식과 어울리는지"** 미각적, 화학적 근거를 들어 설득력 있게 설명한다.

**가이드라인 (Guidelines):**
- **음식 중심 예시:** 모든 답변은 구체적인 요리에 대한 와인 추천으로 이루어져야 한다.
- **상호보완의 원리:** 와인이 음식의 맛을 어떻게 상승시키는지(증폭), 혹은 음식의 단점을 어떻게 가려주는지(보완) 묘사하라.

**예시 (Examples):**
... (생략) ...
'''),
        # 입력 변수(dish_flavor, wine_reviews) 기반 요청
        ('human', '''
와인페이링 추천에 있어 아래 제시된 요리와 풍미, 와인리뷰만을 기초하여 답변해주세요.

## 요리와 풍미 ##
{dish_flavor}

## 와인리뷰 정보 ##
{wine_reviews}
''')
    ])

    llm = init_chat_model('gpt-5.6-luna')
    output_parser = StrOutputParser()

    chain = prompt | llm | output_parser

    return chain # 체인 결과 반환

# def main():
#     dish_flavor_chain = RunnableLambda(describe_dish_flavor)
#     search_wine_review_chain = RunnableLambda(search_wine_review)
#     recommend_wines_chain = RunnableLambda(recommend_wines)


#     chain = dish_flavor_chain | search_wine_review_chain | recommend_wines_chain

#     response = chain.invoke({
#         'text': '',
#         'image_urls': [
#             "https://search.pstatic.net/common/?src=http%3A%2F%2Fblogfiles.naver.net%2FMjAyNTEwMTNfMjM4%2FMDAxNzYwMzYzODc4NDk0.me3_kw-eBIiNd75S0W7XdkBiVbUn78pRz5cVlQWV0EEg.VQcftg1p19qRbhxcvaT9Rk80wha9g1VD0f5yVaIe7cUg.PNG%2FImage_fx_%252866%2529.png&type=sc960_832",
#             "https://search.pstatic.net/common/?src=http%3A%2F%2Fblogfiles.naver.net%2FMjAxODExMjhfMjEy%2FMDAxNTQzNDE1MzEzOTQw.8BT4PzdMbbRctmFFAkLWz3p3G0KywePJxA70TlwTQjcg.8FTmR-SX6Wt7ey27RbV78uzAD8AqedJJKbaAdduuI3Qg.JPEG.story77616%2F20181128_121945.jpg&type=sc960_832"
#         ]
#     })
#     print(response)


# 요리 묘사 -> 와인 검색 -> 추천해주는 통합 스트리밍 체인
def ai_wine_sommelier_rag(query):
    dish_flavor_chain = RunnableLambda(describe_dish_flavor)
    search_wine_review_chain = RunnableLambda(search_wine_review)
    recommend_wines_chain = RunnableLambda(recommend_wines)

    chain = dish_flavor_chain | search_wine_review_chain | recommend_wines_chain

    return chain.stream(query)