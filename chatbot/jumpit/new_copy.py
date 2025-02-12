import pymysql
import os
from typing import Dict, TypedDict, Optional, List, Literal
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import graphviz

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# langsmith
LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')

class State(TypedDict):
    user_input: str  # 사용자 채팅 입력
    chat_history: List[Dict[str, str]]  # 대화 기록
    intent: Optional[str]  # 어떤 기능 사용할건지 저장
    intent_search_job: Optional[str]  # 공고 검색 기능에서의 분기
    job_name: str  # 직무 이름 / 채용 공고 기능에서 사용
    selected_job: int  # 선택한 공고
    job_search: bool  # 공고 탐색 여부
    response: Optional[str]  # 챗봇 답변
    job_results: Optional[List[tuple]]  # 공고 질문 답변 출력 결과
    intent_cover_letter: Optional[str]  # 자기소개서 기능에서의 분기
    cover_letter: Optional[str]  # 작성한 자기소개서
    cover_letter_in: bool  # 자기소개서 DB 저장(작성) 여부
    interview_q: Optional[List[str]]  # 이전 면접 질문 리스트
    interview_in: bool  # 면접 질문 DB 저장 여부
    intent_interview: Optional[str]  # 면접 기능에서의 분기

class JobAssistantBot:
    def __init__(self):
        try:
            self.db = pymysql.connect(
                host=os.getenv('DB_HOST'),
                port=int(os.getenv('DB_PORT')),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                charset="utf8mb4"
            )
            print("DB 연결 성공")

            self.llm = ChatOpenAI(
                model="gpt-4o",
                streaming=True
            )
            print("OpenAI API 초기화 성공")

            self._initialize_prompts()
            print("프롬프트 초기화 성공")

            self.create_saved_jobs_table()
            print("DB 초기화 완료")

        except Exception as e:
            print(f"초기화 중 오류 발생: {e}")
            raise

    # prompt 모아두는 함수
    def _initialize_prompts(self):
        self.intent_template = PromptTemplate.from_template(
            """
            사용자 입력을 분석하여 다음 중 하나로 분류하여 결과로 출력하세요:
            - JOB_SEARCH
              : 직무를 입력하며 채용 공고를 탐색
              : 공고 번호를 입력하며 상세 정보를 요청
            - COVER_LETTER
              : 공고 번호를 입력하며 작성을 요청
              : 사용자가 본인의 경험 혹은 직무 등을 입력
              : 자기소개서 수정을 요청
            - INTERVIEW
              : 면접을 요청
              : 면접 
            - UNKNOWN
              : 서비스와 상관없는 내용 입력

            예시 입력: "백엔드 개발자 공고 알려줘"
            예시 출력: JOB_SEARCH

            사용자 입력: {user_input}
            결과:""")

        self.search_job_prompt = PromptTemplate.from_template(
            """
            사용자의 입력을 분석하여 사용자의 의도를 판단하여 결과로 출력하세요:
            - 채용 공고 제공
              : 사용자가 특정 직무에 대한 채용 공고를 요청하는 경우
            - 상세 정보
              : 사용자가 공고의 상세 내용을 요청하는 경우
            - 관련 없음
              : 채용 공고 탐색 기능과 관계 없는 입력

            상세 정보의 경우 사용자가 입력한 공고 번호를 쉼표로 구분해 함께 출력해주세요.
            채용 공고 제공과 관련 없음의 경우 -1을 함께 출력해주세요.
            
            예시 입력: "첫 번째 공고 우대사항 알려줘"
            예시 출력: 상세 정보, 1

            예시 입력: "프론트엔드 개발자 공고 알려줘"
            예시 출력: 채용 공고 제공, -1

            예시 입력: "오늘 저녁 메뉴 추천해줘"
            예시 출력: 관련 없음, -1

            사용자 입력: {user_input}
            결과:""")

        self.jobname_prompt = PromptTemplate.from_template(
            """
            사용자의 입력을 분석하여 직무 관련 키워드가 포함되어 있는지 판단하세요:
            - include
              : '백엔드', '프론트엔드', '개발자', '프로그래머', 'AI', '인공지능', '데이터' 등 
                직무나 기술 스택 관련 키워드가 포함된 경우
            - not_include
              : 직무 관련 키워드가 전혀 포함되어 있지 않은 경우

            예시 입력: "백엔드 공고 보여줘"
            예시 출력: include

            예시 입력: "공고 알려줘"
            예시 출력: not_include

            사용자 입력: {user_input}
            결과:""")

        self.jobname_extract_prompt = PromptTemplate.from_template(
            """
            사용자의 입력에서 직무, 직업, 개발과 관련된 모든 키워드를 추출해주세요. 
            'AI', '백엔드', '프론트엔드', '개발자', '프로그래머'와 같은 직무명, 기술 스택, 직업과 관련된 키워드들을 포함해야 합니다.
            결과를 쉼표로 구분된 키워드 문자열로 반환해주세요.

            '공고', '보여줘' 등은 키워드로 포함하지 마세요.

            사용자 입력: {user_input}
            결과:""")
        # 로봇, 로보틱스 등 개발자와 조금 거리가 먼 단어는 키워드로 분류하지 않음
        
        self.moreinfo_extract_prompt = PromptTemplate.from_template(
            """
            사용자의 입력에서 어떤 상세 정보를 원하는지 추출해주세요.
            - 제목
            - 회사명
            - 사용기술
            - 근무지역
            - 근로조건
            - 모집기간
            - 링크
            - 주요업무
            - 자격요건
            - 우대사항
            - 복지_및_혜택
            - 채용절차
            - 학력
            - 근무지역_상세
            - 마감일자

            여러 가지 정보를 원했다면 결과를 쉼표로 구분된 키워드 문자열로 반환해주세요.
            사용자가 입력을 상세 정보, 모든 상세 정보 등 상세 정보 전부를 원하는 요청을 입력했다면,
            모든 키워드를 쉼표로 구분하여 반환해주세요.

            예시 입력: "첫 번째 공고의 주요 업무와 자격요건 알려줘"
            예시 출력: 주요업무, 자격요건

            예시 입력: "상세 정보"
            예시 출력: 제목, 회사명, 사용기술, 근무지역, 근로조건, 모집기간, 링크, 주요업무, 자격요건, 우대사항, 복지_및_혜택, 채용절차, 학력, 근무지역_상세, 마감일자
            
            사용자 입력: {user_input}
            결과:""")
        
        self.natural_response = PromptTemplate.from_template(
            """
            사용자에게 채용 공고의 상세 정보를 자연스럽게 전달해주세요.
            상세 정보: {extracted_info}
            """)
        
        self.cover_letter_prompt = PromptTemplate.from_template(
            """
            사용자의 입력을 분석하여 사용자의 의도를 판단하여 결과로 출력하세요:
            - 자기소개서 작성
              : 사용자가 자기소개서 작성을 요청하는 경우
              : 사용자가 자신의 경험, 프로젝트, 기술 스택, 직무와 관련된 내용을 입력한 경우 (명확한 요청이 없어도 포함)
              : 사용자가 특정 경험을 입력한 경우
              : 숫자를 입력한 경우
            - 자기소개서 수정
              : 사용자가 자기소개서 수정을 요청하는 경우
              : 특정 문장을 수정해달라고 요청하는 경우
            - 관련 없음
              : 자기소개서 기능과 관계 없는 입력 (일반적인 질문, 잡담 등)

            사용자 입력에 숫자와 관련된 단어 혹은 숫자가 있다면 해당 숫자를 쉼표로 구분해 함께 출력해주세요.
            숫자 관련 단어 혹은 숫자가 없는 경우 -1을 함께 출력해주세요.

            예시 입력: 첫 번째 공고로 자기소개서 작성해줘.
                       나는 SQL을 사용해서 데이터를 분석하는 프로젝트를 진행했고, 그 프로젝트를 통해 SQL 활용법을 익혔어.
                       이 경험을 활용해서 자기소개서 작성해줘
            예시 출력: 자기소개서 작성, 1

            예시 입력: AI 개발자 직무에 지원하려고 해
                       나는 LLM을 활용해서 챗봇을 개발하는 프로젝트를 진행했고, 그 프로젝트를 통해 LLM을 활용하는 방법을 배웠어.
                       이 경험을 활용해서 자기소개서 작성해줘
            예시 출력: 자기소개서 작성, -1

            예시 입력: 직무 역량에서 A 프로젝트의 a 내용을 추가해줘
            예시 출력: 자기소개서 수정, -1

            사용자 입력: {user_input}
            결과:""")

        self.experience_prompt = PromptTemplate.from_template(
            """
            사용자의 입력을 분석하여 경험이 포함되어 있는지 판단하세요:
            - experience_include
              : 경험이 포함되어 있는 경우

            경험은 프로젝트, 경력 등 사용자가 이전에 수행했던 내용을 포함해야 합니다.
            경험이 포함되어 있는 경우 "experience_include"를,
            포함되어 있지 않은 경우 "experience_exclude"를 결과로 출력하세요.
            
            사용자 입력: {user_input}
            결과:""")

        self.experience_prompt_without_job = PromptTemplate.from_template(
            """
            사용자의 입력을 분석하여 직무와 경험이 포함되어 있는지 판단하세요:
            - job_include
              : 직무가 포함되어 있는 경우
            - experience_include
              : 경험이 포함되어 있는 경우
            - all_include
              : 직무와 경험이 모두 포함되어 있는 경우
            - not_include
              : 직무와 경험이 모두 포함되어 있지 않는 경우

            직무는 'AI', '백엔드', '프론트엔드', '개발자'와 같은 키워드들을 포함해야 합니다.
            경험은 프로젝트, 경력 등 사용자가 이전에 수행했던 내용을 포함해야 합니다.
            
            사용자 입력: {user_input}
            결과:""")
        
        self.cover_letter_write = PromptTemplate.from_template(
            """
            [채용 공고 정보]
            - 공고 이름: {job_name}
            - 기술 스택: {tech_stack}
            - 주요 업무: {job_desc}
            - 자격 요건: {requirements}
            - 우대 사항: {preferences}

            [사용자 경험 및 직무]
            {user_input}

            자기소개서는 다음 4가지 항목을 포함해야 합니다:
            1. 지원 동기
            2. 성격의 장단점
            3. 직무 역량
            4. 입사 후 포부

            각 항목을 사용자의 경험과 채용 공고 정보를 포함하여 구체적으로 작성하세요. 
            각 항목 별로 공백을 포함하지 않고 500자에서 700자 사이로 작성해주세요.    
            결과:""")
        
        self.cover_letter_write_without_job = PromptTemplate.from_template(
            """
            [사용자 경험 및 직무]
            {user_input}

            자기소개서는 다음 4가지 항목을 포함해야 합니다:
            1. 지원 동기
            2. 성격의 장단점
            3. 직무 역량
            4. 입사 후 포부

            각 항목을 사용자의 경험과 직무 정보를 포함하여 구체적으로 작성하세요. 
            각 항목마다 공백을 포함하지 않고 700자 내외로 작성해주세요.
	        네 항목이므로 총 글자수가 공백을 포함하지 않고 3000자 내외로 나와야 합니다.
            결과:""")
        
        self.cover_letter_refine = PromptTemplate.from_template(
            """
            [기존 자기소개서 내용]
            {previous_response}

            [사용자 수정 요청]
            {user_input}

            사용자가 입력한 수정 요청을 반영하여 기존 자기소개서 내용을 수정해주세요. 
            기존 내용의 일관성을 유지하면서 수정사항을 반영해주세요.            
            결과: """)

        self.interview_intent = PromptTemplate.from_template(
            """
            사용자의 입력을 분석하여 사용자의 의도를 판단하여 결과로 출력하세요:
            - 인성 면접
              : 사용자가 인성 면접을 요청하는 경우
              : 사용자 입력에 "인성"이 포함되는 경우
            - 기술 면접
              : 사용자가 기술 면접을 요청하는 경우
              : 사용자 입력에 "기술"이 포함되는 경우
            - 종료
              : 그만할게 등 사용자가 면접 종료를 희망하는 경우
              : 사용자 입력에 "종료"가 포함되는 경우
            - 관련 없음
              : 면접 연습과 관계 없는 입력 (일반적인 질문, 잡담 등)

            예시 입력: 인성 질문으로 해줘
            예시 출력: 인성 면접

            예시 입력: 기술 질문
            예시 출력: 기술 면접

            사용자 입력: {user_input}
            결과: """)
        
        self.interview_tenacity = PromptTemplate.from_template(
            """
            당신은 인성 면접관입니다. 다음 가이드라인에 따라 면접을 진행해주세요:

            1. 답변 분석:
            - 사용자의 이전 답변을 꼼꼼히 분석합니다
            - 답변의 핵심 내용과 특징을 파악합니다
            - 추가 설명이 필요한 부분을 확인합니다

            2. 후속 질문 생성:
            - 이전 답변과 자연스럽게 연결되는 질문을 생성합니다
            - 답변에서 언급된 구체적인 내용을 기반으로 질문합니다
            - 이전 DB 내역의 질문과 중복되지 않도록 합니다

            3. 질문 스타일:
            - "~하시군요"나 "흥미로운 답변이네요" 등으로 답변에 대한 반응을 먼저 보입니다
            - 그 후 "그렇다면" 또는 "이어서"로 자연스럽게 다음 질문으로 넘어갑니다
            - 대화하듯 자연스럽고 부드러운 어투를 사용합니다

            예시 입력: "대학 시절 프로젝트 리더를 맡아 팀원들과 함께 성공적으로 프로젝트를 완수했습니다."
            예시 출력: 리더십을 발휘하신 좋은 경험이시군요. 그렇다면 팀 리더로서 가장 어려웠던 순간은 언제였고, 어떻게 극복하셨나요?

            사용자 입력: {user_input}
            DB 내역: {interview_history}
            결과: """)

        self.interview_technology = PromptTemplate.from_template(
            """
            당신은 기술 면접관입니다. 다음 가이드라인에 따라 면접을 진행해주세요:

            1. 답변 분석:
            - 사용자의 이전 답변에서 기술적 이해도를 파악합니다
            - 자기소개서에 언급된 기술과 프로젝트를 기반으로 질문을 생성합니다
            - 추가 설명이 필요한 기술적 부분을 확인합니다

            2. 후속 질문 생성:
            - 이전 답변에서 언급된 기술이나 개념을 더 깊이 파고드는 질문을 합니다
            - 실제 문제 해결 능력을 확인할 수 있는 구체적인 시나리오를 제시합니다
            - 이전 DB 내역의 질문과 중복되지 않도록 합니다

            3. 질문 스타일:
            - "좋은 설명이었습니다"나 "이해했습니다" 등으로 답변에 대한 피드백을 먼저 줍니다
            - "조금 더 구체적으로 들어가보면" 등으로 자연스럽게 심화 질문으로 넘어갑니다
            - 전문가 대 전문가의 대화처럼 기술적인 내용을 자연스럽게 주고받습니다

            예시 입력: "저는 Node.js의 비동기 처리를 위해 주로 async/await를 사용합니다."
            예시 출력: async/await에 대해 잘 이해하고 계시군요. 그렇다면 Promise와 비교했을 때 async/await의 장단점은 무엇이라고 생각하시나요?

            사용자 입력: {user_input}
            DB 내역: {interview_history}
            자기소개서: {cover_letter}
            결과: """)

    # 분기점: intent 분류
    def classify_intent(self, state: State) -> State:
        intent = str(self.llm.invoke(self.intent_template.format(user_input=state["user_input"])).content).strip()
        if state["interview_in"] and state["intent_interview"]:
            intent = "INTERVIEW"
        
        if intent not in ["JOB_SEARCH", "COVER_LETTER", "INTERVIEW", "UNKNOWN"]:
            intent = "UNKNOWN"
        print(f"Classified intent: {intent}")  # 디버깅용 출력
        return {**state, "intent": intent}

    # 저장된 공고를 위한 테이블 생성
    def create_saved_jobs_table(self):
        cursor = self.db.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS saved_job_posting (
            id INT AUTO_INCREMENT PRIMARY KEY,
            제목 VARCHAR(255),
            회사명 VARCHAR(255),
            사용기술 TEXT,
            근무지역 VARCHAR(255),
            근로조건 VARCHAR(255),
            모집기간 VARCHAR(255),
            링크 TEXT,
            저장일시 DATETIME DEFAULT CONVERT_TZ(NOW(), 'UTC', 'Asia/Seoul'),
            주요업무 TEXT,
            자격요건 TEXT,
            우대사항 TEXT,
            복지_및_혜택 TEXT,
            채용절차 TEXT,
            학력 VARCHAR(255),
            근무지역_상세 VARCHAR(255),
            마감일자 VARCHAR(255)
        )
        """

        cursor.execute(create_table_query)
        
        # 기존 데이터 삭제
        delete_data_query = "DELETE FROM saved_job_posting"
        cursor.execute(delete_data_query)
        
        # AUTO_INCREMENT 값 초기화
        reset_auto_increment_query = "ALTER TABLE saved_job_posting AUTO_INCREMENT = 1"
        cursor.execute(reset_auto_increment_query)

        self.db.commit()
        cursor.close()

    # 채용 공고 불러오기
    def search_job(self, state: State) -> State:
        cursor = self.db.cursor()
        search_keyword = str(self.llm.invoke(self.jobname_extract_prompt.format(user_input=state["user_input"])).content).strip()
        print(search_keyword)
        search_keywords = [kw.strip() for kw in search_keyword.split(',') if kw.strip()]
        print(search_keywords)
        
        if not search_keywords:
            return {**state, "response": "검색할 직무 키워드를 입력해주세요."}

        conditions = " OR ".join(["(제목 LIKE %s OR 사용기술 LIKE %s)" for _ in search_keywords])
        params = [f"%{keyword}%" for keyword in search_keywords for _ in range(2)]
        print(conditions, params)

        query = f"""
        SELECT 제목, 회사명, 사용기술, 근무지역, 근로조건, 모집기간, 링크,
            주요업무, 자격요건, 우대사항, 복지_및_혜택, 채용절차, 
            학력, 근무지역_상세, 마감일자
        FROM job_posting_new
        WHERE {conditions}
        """
        
        cursor.execute(query, params)
        result = cursor.fetchall()
        cursor.close()
        # return result
        return {**state, "job_results": result}
    
    # 검색된 공고들을 saved_job_posting 테이블에 저장
    def save_jobs_to_table(self, jobs):
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM saved_job_posting")
        self.db.commit()

        insert_query = """
        INSERT INTO saved_job_posting
        (제목, 회사명, 사용기술, 근무지역, 근로조건, 모집기간, 링크, 
        주요업무, 자격요건, 우대사항, 복지_및_혜택, 채용절차,
        학력, 근무지역_상세, 마감일자)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, 
                %s, %s, %s)
        """

        for job in jobs:
            cursor.execute(insert_query, job)
        
        self.db.commit()
        cursor.close()

    # 채용 공고 제공 기능
    def search_job_chat(self, state: State) -> State:
        search_road, num = self.llm.invoke(self.search_job_prompt.format(user_input=state["user_input"])).content.split(',')
        num = int(num.strip())
        print('채용공고 분기:', search_road, num)
        response = ""
        
        if search_road == "채용 공고 제공":
            jobname_validate = str(self.llm.invoke(self.jobname_prompt.format(user_input=state["user_input"])).content).strip()
            print(jobname_validate)
            if jobname_validate == "not_include":
                return {**state, "response": "탐색을 원하는 직무를 입력해주세요."}
            else:
                self.create_saved_jobs_table()
                print("테이블 생성 완료")
                search_result = self.search_job(state)
                print("공고 검색 완료")
                
                # 에러 응답이 있는 경우 그대로 반환
                if search_result.get("response") and search_result.get("response") == "검색할 직무 키워드를 입력해주세요.":
                    return search_result
                
                # 검색 결과 가져오기
                result = search_result.get("job_results", [])
                self.save_jobs_to_table(result)
                
                if result:
                    for i, job in enumerate(result[:10], 1):
                        response += (
                            f"{i}.  {job[0]}\n"
                            f"회사명: {job[1]}\n"
                            f"기술스택: {job[2]}\n"
                            f"근무지: {job[3]}\n"
                            f"조건: {job[4]}\n"
                            f"모집기간: {job[5]}\n"
                            f"[지원 링크] ({job[6]})\n\n"
                        )
                    response += (
                        "상세 정보 (주요 업무, 자격 요건, 우대사항, 복지 및 혜택, 채용절차, 학력, 근무지역 상세, 마감일자) 를 알고 싶으시면 원하시는 공고와 키워드를 입력해주세요.\n"
                        "모든 상세 정보를 알고 싶으시면 원하시는 공고 번호와 함께 상세 정보라고 입력해주세요.\n"
                        "공고를 선택해 맞춤형 자기소개서 초안을 작성하고 싶으시면 원하시는 공고 번호와 자기소개서 작성을 입력해주세요.\n"
                        "공고를 선택해 맞춤형 면접 연습을 진행하고 싶으시면 원하시는 공고 번호와 면접 연습을 입력해주세요."
                    )
                    return {**state, "response": response, "selected_job": num, "job_search": True}
                else:
                    return {**state, "response": "관련된 채용 공고를 찾지 못했습니다."}

        elif search_road == "상세 정보":
            moreinfo = self.llm.invoke(self.moreinfo_extract_prompt.format(user_input=state["user_input"])).content
            moreinfo_list = moreinfo.split(',')
            field_name = ', '.join(mi.strip() for mi in moreinfo_list)
            moreinfo_query = f"""
            SELECT {field_name} FROM saved_job_posting
            ORDER BY id ASC
            LIMIT 1 OFFSET %s
            """

            cursor = self.db.cursor()
            cursor.execute(moreinfo_query, (num-1,))
            result = cursor.fetchone()
            cursor.close()
            if result:
                # 조회된 데이터를 LLM에 전달할 문자열로 구성
                extracted_info = "\n".join(f"{name}: {detail}" for name, detail in zip(moreinfo_list, result))

                # LLM이 자연스럽게 답변 생성
                response = str(self.llm.invoke(self.natural_response.format(extracted_info=extracted_info)).content).strip()

                return {**state, "response": response, "selected_job": num, "job_search": True}
            else:
                return {**state, "response": "선택하신 상세 정보가 없습니다."}

        elif search_road == "관련 없음":
            return {**state, "intent_search_job": "UNKNOWN"}
    
    # 자기소개서 저장을 위한 테이블 생성
    def create_saved_cover_letter_table(self):
        cursor = self.db.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS saved_cover_letter (
            id INT AUTO_INCREMENT PRIMARY KEY,
            자기소개서 TEXT,
            저장일시 DATETIME DEFAULT CONVERT_TZ(NOW(), 'UTC', 'Asia/Seoul')
        )
        """

        cursor.execute(create_table_query)

        self.db.commit()
        cursor.close()

    # 자기소개서 저장
    def save_cover_letter_to_table(self, cover_letter):
        cursor = self.db.cursor()
        query = """
        INSERT INTO saved_cover_letter (자기소개서)
        VALUES (%s)
        """

        cursor.execute(query, cover_letter)
        
        self.db.commit()
        cursor.close()
            
    # 지정한 공고 불러오기
    def search_select_job(self, state: State) -> Dict:
        cursor = self.db.cursor()
        query = """
        SELECT 제목, 사용기술, 주요업무, 자격요건, 우대사항
        FROM saved_job_posting
        WHERE id = %s
        """

        print(query)
        cursor.execute(query, (state['selected_job'], ))
        result = cursor.fetchall()
        cursor.close()

        print(result)
        if result:
            return {
                'job_name': result[0][0],
                'tech_stack': result[0][1],
                'job_desc': result[0][2],
                'requirements': result[0][3],
                'preferences': result[0][4]
            }
        return None

    # 가장 최근에 생성한 자기소개서 불러오기
    def search_cover_letter(self, state: State) -> State:
        cursor = self.db.cursor()
        query = f"""
        SELECT 자기소개서
        FROM saved_cover_letter
        ORDER BY 저장일시 DESC
        LIMIT 1
        """

        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()

        if result:
            return {**state, "cover_letter": result[0]}  # 첫 번째 컬럼값만 반환
        return {**state, "cover_letter": None}
    
    # 자기소개서 기능
    def cover_letter_chat(self, state: State) -> State:
        try:
            cl_road, num = str(self.llm.invoke(
                self.cover_letter_prompt.format(user_input=state["user_input"])
            ).content).split(',')

            cl_road = cl_road.strip()
            num = int(num.strip())
        except Exception as e:
            print(f'에러 발생: {e}')
        print("자기소개서 분기", cl_road, num)
        response = ""
        
        if num and num > 0:
            state['selected_job'] = num

        if cl_road == "자기소개서 작성":
            if state["job_search"]:
                print('채용 공고 검색함')

                if not state['selected_job'] or state['selected_job'] < 0:
                    return {**state, "response": "공고 번호를 입력해주세요."}

                job_exp = str(self.llm.invoke(
                    self.experience_prompt.format(user_input=state["user_input"])
                ).content).strip()
                print('자기소개서 분기: ', job_exp)
                
                if job_exp in ['experience_include']:
                    job_info = self.search_select_job(state)
                    if not job_info:
                        return {**state, "response": "선택한 공고를 찾을 수 없습니다."}
                        
                    cover_letter_writing = str(self.llm.invoke(
                        self.cover_letter_write.format(**job_info, user_input=state["user_input"])
                    ).content).strip()
                    
                    self.create_saved_cover_letter_table()
                    self.save_cover_letter_to_table(cover_letter_writing)

                    response += cover_letter_writing
                    response += (
                        "\n\n수정된 자기소개서의 추가적인 수정을 원하시면 수정 요청 사항을 입력해주세요.\n"
                        "인성 면접 연습을 진행하고 싶으시면 인성 면접 연습을 입력해주세요.\n"
                        "작성된 자기소개서로 맞춤형 기술 면접 연습을 진행하고 싶으시면 기술 면접 연습을 입력해주세요."
                    )
                    return {**state, "response": response, "cover_letter": cover_letter_writing, "cover_letter_in": True, "selected_job": num}
                else:
                    return {**state, "response": "자기소개서 작성을 위해 경험을 입력해주세요.", "selected_job": num}
                    
            else:
                print('채용 공고 검색하지 않음')
                job_exp = str(self.llm.invoke(self.experience_prompt_without_job.format(user_input=state["user_input"])).content).strip()
                if job_exp == 'all_include':
                    job_info = self.search_select_job(num)
                    cover_letter_writing = str(self.llm.invoke(self.cover_letter_write_without_job.format(user_input=state["user_input"])).content).strip()
                    print(cover_letter_writing)

                    self.create_saved_cover_letter_table()
                    self.save_cover_letter_to_table(cover_letter_writing)

                    response += cover_letter_writing
                    response += (
                        "\n\n수정된 자기소개서의 추가적인 수정을 원하시면 수정 요청 사항을 입력해주세요.\n"
                        "인성 면접 연습을 진행하고 싶으시면 인성 면접 연습을 입력해주세요.\n"
                        "작성된 자기소개서로 맞춤형 기술 면접 연습을 진행하고 싶으시면 기술 면접 연습을 입력해주세요."
                    )
                    return {**state, "response": cover_letter_writing, "cover_letter": cover_letter_writing, "cover_letter_in": True, "selected_job": num}
                elif job_exp == 'experience_include':
                    return {**state, "response": "자기소개서에 반영할 직무를 입력해주세요.", "selected_job": num}
                elif job_exp == 'job_include':
                    return {**state, "response": "자기소개서에 반영할 경험을 입력해주세요.", "selected_job": num}
                elif job_exp == 'not_include':
                    return {**state, "response": "자기소개서에 반영할 직무와 경험을 입력해주세요.", "selected_job": num}

        elif cl_road == "자기소개서 수정":
            if not state["cover_letter_in"]:
                return {**state, "response": "작성된 자기소개서가 없습니다. 자기소개서를 먼저 작성하고 이용해주세요."}
                
            refine_cover_letter = str(self.llm.invoke(
                self.cover_letter_refine.format(
                    user_input=state["user_input"],
                    previous_response=state["cover_letter"]
                )
            ).content).strip()
            
            self.save_cover_letter_to_table(refine_cover_letter)

            response += refine_cover_letter
            response += (
                "\n\n수정된 자기소개서의 추가적인 수정을 원하시면 수정 요청 사항을 입력해주세요.\n"
                "인성 면접 연습을 진행하고 싶으시면 인성 면접 연습을 입력해주세요.\n"
                "작성된 자기소개서로 맞춤형 기술 면접 연습을 진행하고 싶으시면 기술 면접 연습을 입력해주세요."
            )
            return {**state, "response": refine_cover_letter, "cover_letter": refine_cover_letter}

        elif cl_road == "관련 없음":
            return {**state, "intent_cover_letter": "UNKNOWN"}

    # 면접 질문 저장을 위한 DB 생성
    def create_saved_interview_question_table(self):
        cursor = self.db.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS saved_interview_question (
            id INT AUTO_INCREMENT PRIMARY KEY,
            면접질문 TEXT,
            저장일시 DATETIME DEFAULT CONVERT_TZ(NOW(), 'UTC', 'Asia/Seoul')
        )
        """

        cursor.execute(create_table_query)

        self.db.commit()
        cursor.close()

    # 면접 질문 저장
    def save_interview_question_to_table(self, interview_question):
        cursor = self.db.cursor()
        query = """
        INSERT INTO saved_interview_question (면접질문)
        VALUES (%s)
        """

        cursor.execute(query, interview_question)
        
        self.db.commit()
        cursor.close()
    
    # 면접 질문들 불러오기
    def search_interview_question(self, state: State) -> State:
        try:
            cursor = self.db.cursor()
            query = """
            SELECT 면접질문
            FROM saved_interview_question
            """

            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()

            # 결과가 없을 경우 빈 리스트 반환
            if not result:
                return {**state, "interview_q": []}
            
            # 결과가 있는 경우 리스트로 변환하여 반환
            questions = [row[0] for row in result]
            return {**state, "interview_q": questions}
        except Exception as e:
            print(f'에러 발생: {e}')
    
    def interview_chat(self, state: State) -> State:
        try:
            self.create_saved_interview_question_table()
            
            # 현재 진행 중인 면접 타입 확인
            current_intent = state.get('intent_interview')
            
            # 이미 면접이 진행 중인 경우
            if current_intent in ['TENACITY', 'TECHNOLOGY']:
                if "종료" in state["user_input"].lower():
                    return {**state, "response": "면접 연습을 종료합니다.", "intent_interview": "END", "interview_in": False}
                return {**state, "intent_interview": current_intent, "interview_in": True}
            
            # 새로운 면접 시작 시에만 의도 분류
            interview_road = str(self.llm.invoke(
                self.interview_intent.format(user_input=state["user_input"])
            ).content).strip()
            print("면접 분기: ", interview_road)

            if interview_road == '인성 면접':
                return {**state, "response": "인성 면접을 시작합니다. \n1분 자기소개 시작해주세요.", "intent_interview": "TENACITY", "interview_in": True}
            elif interview_road == '기술 면접':
                if not state.get('cover_letter_in'):
                    return {**state, "response": "기술 면접을 위해서는 먼저 자기소개서가 필요합니다.", "intent_interview": "END"}
                return {**state, "response": "기술 면접을 시작합니다. \n1분 자기소개 시작해주세요.", "intent_interview": "TECHNOLOGY", "interview_in": True}
            elif interview_road == '종료':
                return {**state, "response": "면접 연습을 종료합니다.", "intent_interview": "END"}
            else:
                return {**state, "intent_interview": "UNKNOWN"}
                
        except Exception as e:
            print(f'에러 발생: {e}')

    # 인성 질문 추출
    def tenacity_interview(self, state: State) -> State:
        try:
            if state['interview_in']:
                self.create_saved_interview_question_table()
                search_result = self.search_interview_question(state)
                print("면접 질문 검색 완료")

            questions = search_result.get("interview_q", [])
            
            response = str(self.llm.invoke(self.interview_tenacity.format(user_input=state['user_input'], interview_history=questions)).content).strip()
            self.save_interview_question_to_table(response)
            return {**state, "response": response, "intent_interview": "TENACITY", "interview_in": True}
        except Exception as e:
            print(f'에러 발생: {e}')

    # 기술 질문 추출
    def technology_interview(self, state: State) -> State:
        try:
            if state['interview_in']:
                self.create_saved_interview_question_table()
                search_result = self.search_interview_question(state)
                print("면접 질문 검색 완료")

            if state['cover_letter_in']:
                self.create_saved_cover_letter_table()
                state = self.search_cover_letter(state)
                if not state['cover_letter']: 
                    return {**state, "response": "자기소개서를 찾을 수 없습니다.", "intent_interview": "END"}
            else:
                return {**state, "response": "자기소개서가 없습니다.", "intent_interview": "END"}
            
            questions = search_result.get("interview_q", [])
            
            response = str(self.llm.invoke(self.interview_technology.format(user_input=state['user_input'], interview_history=questions, cover_letter=state['cover_letter'])).content).strip()
            self.save_interview_question_to_table(response)
            return {**state, "response": response, "intent_interview": "TECHNOLOGY", "interview_in": True}
        except Exception as e:
            print(f'에러 발생: {e}')


    def unknown_message(self, state: State) -> State:
        response = "시스템과 관련 없는 질문입니다. 다른 질문을 입력해주세요."
        return {**state, "response": response}

    def create_workflow(self) -> StateGraph:
        workflow = StateGraph(State)

        workflow.add_node("classify_intent", self.classify_intent)
        workflow.add_node("search_job_chat", self.search_job_chat)
        workflow.add_node("cover_letter_chat", self.cover_letter_chat)
        workflow.add_node("interview_chat", self.interview_chat)
        workflow.add_node("unknown_message", self.unknown_message)
        workflow.add_node("tenacity_interview", self.tenacity_interview)
        workflow.add_node("technology_interview", self.technology_interview)

        workflow.set_entry_point("classify_intent")

        workflow.add_conditional_edges(
            "classify_intent",
            lambda state: state.get('interview_intent', state.get('intent', 'UNKNOWN')),
            {
                "JOB_SEARCH": "search_job_chat",
                "COVER_LETTER": "cover_letter_chat",
                "INTERVIEW": "interview_chat", 
                # "TENACITY": "tenacity_interview",
                # "TECHNOLOGY": "technology_interview",
                "UNKNOWN": "unknown_message"
            }
        )

        workflow.add_conditional_edges(
            "search_job_chat",
            lambda state: (
                state.get('intent_search_job') 
                if state.get('intent_search_job') in ['UNKNOWN'] 
                else "END"
            ),
            {
                "UNKNOWN": "unknown_message",
                "END": END
            }
        )

        workflow.add_conditional_edges(
            "cover_letter_chat",
            lambda state: (
                state.get('intent_cover_letter')
                if state.get('intent_cover_letter') in ['UNKNOWN']
                else 'END'
            ),
            {
                "UNKNOWN": "unknown_message",
                "END": END
            }
        )

        workflow.add_conditional_edges(
            "interview_chat",
            lambda state: (
                state.get('intent_interview')
                if state.get('intent_interview') in ['TENACITY', 'TECHNOLOGY', 'UNKNOWN']
                else 'END'
            ),
            {
                "TENACITY": "tenacity_interview",
                "TECHNOLOGY": "technology_interview",
                "END": END
            }
        )

        workflow.add_conditional_edges(
            "tenacity_interview",
            lambda state: "END" if not state.get('interview_in') else "END",
            {
                "END": END
            }
        )

        workflow.add_conditional_edges(
            "technology_interview",
            lambda state: "END" if not state.get('interview_in') else "END",
            {
                "END": END
            }
        )

        # workflow.add_edge("tenacity_interview", END)
        # workflow.add_edge("technology_interview", END)
        workflow.add_edge("unknown_message", END)

        return workflow.compile()
    
    def show_graph(self, workflow):
        try:
            img_data = workflow.get_graph().draw_mermaid_png()
            with open("graph.png", "wb") as f:
                f.write(img_data)
            print("그래프 생성 완료")
        except Exception as e:
            print(f"그래프 생성 중 오류 발생: {e}")
            # 그래프 생성 실패해도 프로그램은 계속 실행
            pass

def main():
    # 봇 인스턴스 생성
    bot = JobAssistantBot()
    workflow = bot.create_workflow()
    
    # 워크플로우 그래프 시각화
    bot.show_graph(workflow)
    
    print("Job Assistant Bot이 시작되었습니다. 종료하려면 'quit' 또는 'exit'를 입력하세요.")

    # 초기 상태 설정
    state = {
        "user_input": "",
        "chat_history": [],
        "intent": None,
        "intent_search_job": None,
        "job_name": "",
        "selected_job": None,
        "job_search": False, 
        "response": None,
        "job_results": [],
        "intent_cover_letter": None,
        "cover_letter": None,
        "cover_letter_in": False,
    }

    while True:
        user_input = input("\n사용자: ")
        
        if user_input.lower() in ['quit', 'exit']:
            print("챗봇을 종료합니다.")
            break
            
        # 현재 user_input으로 state 업데이트
        state["user_input"] = user_input
        
        try:
            # workflow 실행 결과를 새로운 state로 업데이트
            result = workflow.invoke(state)
            # 결과로 받은 state를 다음 반복에 사용하기 위해 업데이트
            state.update(result)
            print(state)
            
            # 응답 출력
            if state.get("response"):
                print(f"Bot: {state['response']}")
            else:
                print("Bot: 죄송합니다. 처리 중 문제가 발생했습니다.")
                
        except Exception as e:
            print(f"오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    main()