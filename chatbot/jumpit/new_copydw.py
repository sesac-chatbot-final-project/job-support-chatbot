import pymysql
import os
from typing import Dict, TypedDict, Optional, List, Literal
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import graphviz
from django.contrib.auth.models import User

# Amazon Polly 관련 라이브러리 (이제 사용하지 않을 수도 있음)
import boto3
import uuid

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')

# Amazon Polly TTS 함수는 더 이상 사용하지 않으므로 주석 처리하거나 제거 가능
# def synthesize_speech(text: str) -> str:
#     polly = boto3.client(
#         'polly',
#         aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
#         aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
#         region_name=os.getenv('AWS_REGION')
#     )
#     response = polly.synthesize_speech(
#         Text=text,
#         OutputFormat='mp3',
#         VoiceId='Seoyeon'
#     )
#     filename = f"speech_{uuid.uuid4().hex}.mp3"
#     output_dir = os.path.join("static", "tts")
#     os.makedirs(output_dir, exist_ok=True)
#     output_path = os.path.join(output_dir, filename)
#     with open(output_path, "wb") as f:
#         f.write(response["AudioStream"].read())
#     return f"/static/tts/{filename}"

class State(TypedDict):
    user_id: str
    user_input: str
    chat_history: List[Dict[str, str]]
    intent: Optional[str]
    intent_search_job: Optional[str]
    job_name: str
    selected_job: int
    job_search: bool
    response: Optional[str]
    job_results: Optional[List[tuple]]
    intent_cover_letter: Optional[str]
    cover_letter: Optional[str]
    cover_letter_in: bool
    interview_q: Optional[List[str]]
    interview_in: bool
    intent_interview: Optional[str]

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
            
            self.create_and_save_customer_db()
            self.create_saved_jobs_table()
            self.create_saved_cover_letter_table()
            self.create_saved_interview_question_table()
            print("DB 초기화 완료")
        except Exception as e:
            print(f"초기화 중 오류 발생: {e}")
            raise

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
            'AI', '백엔드', '프론트엔드', '개발자', '프로그래머', '로봇', '반도체'와 같은 키워드들을 포함해야 합니다.
            단어 별로 끊어서 반환해주세요. (예시: 데이터 분석 → 데이터, 분석 / 펌웨어 개발 → 펌웨어, 개발)
            결과를 쉼표로 구분된 키워드 문자열로 반환해주세요.

            '공고', '보여줘' 등은 키워드로 포함하지 마세요.

            사용자 입력: {user_input}
            결과: """)
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
            사용자가 입력을 상세 정보, 모든 상세 정보 등 상세 정보 전부를 원하는 경우, 
            모든 키워드를 쉼표로 구분하여 반환해주세요.

            예시 입력: "첫 번째 공고의 주요 업무와 자격요건 알려줘"
            예시 출력: 주요업무, 자격요건

            예시 입력: "상세 정보"
            예시 출력: 제목, 회사명, 사용기술, 근무지역, 근로조건, 모집기간, 링크, 주요업무, 자격요건, 우대사항, 복지_및_혜택, 채용절차, 학력, 근무지역_상세, 마감일자
            
            사용자 입력: {user_input}
            결과:""")
        self.natural_response = PromptTemplate.from_template(
            """
            사용자에게 채용 공고의 상세 정보를 아래 형식대로 자연스럽게 전달해주세요.
            상세 정보: {extracted_info}
            형식: [상세 정보 제목] \n 상세 정보 내용
            결과: """)
        self.cover_letter_prompt = PromptTemplate.from_template(
            """
            사용자의 입력을 분석하여 사용자의 의도를 판단하여 결과로 출력하세요:
            - 자기소개서 작성
              : 사용자가 자기소개서 작성을 요청하는 경우
              : 사용자가 자신의 경험, 프로젝트, 기술 스택, 직무와 관련된 내용을 입력하는 경우
              : 사용자가 특정 경험을 입력한 경우
              : 숫자를 입력한 경우
            - 자기소개서 수정
              : 사용자가 자기소개서 수정을 요청하는 경우
              : 특정 문장을 수정해달라고 요청하는 경우
            - 관련 없음
              : 자기소개서 기능과 관계 없는 입력 (일반적인 질문, 잡담 등)

            사용자 입력에 숫자 혹은 관련 단어가 있다면 해당 숫자를 쉼표로 구분해 함께 출력해주세요.
            숫자 관련 내용이 없으면 -1을 출력해주세요.

            예시 입력: "첫 번째 공고로 자기소개서 작성해줘. SQL 프로젝트 경험을 활용해서 작성해줘"
            예시 출력: 자기소개서 작성, 1

            사용자 입력: {user_input}
            결과:""")
        self.experience_prompt = PromptTemplate.from_template(
            """
            사용자의 입력을 분석하여 경험이 포함되어 있는지 판단하세요:
            - experience_include
              : 경험이 포함되어 있는 경우

            경험은 프로젝트, 경력 등을 포함해야 합니다.
            포함되어 있으면 "experience_include", 아니면 "experience_exclude"를 출력하세요.
            
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
              : 직무와 경험 모두 포함된 경우
            - not_include
              : 둘 다 포함되지 않은 경우

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

            자기소개서는 다음 4가지를 포함해야 합니다:
            1. 지원 동기
            2. 성격의 장단점
            3. 직무 역량
            4. 입사 후 포부

            각 항목을 구체적으로 아래 형식에 맞춰 작성해주세요 (500~700자 내외).
            형식: [질문 이름] \n 내용
            결과:""")
        self.cover_letter_write_without_job = PromptTemplate.from_template(
            """
            [사용자 경험 및 직무]
            {user_input}

            자기소개서는 다음 4가지를 포함해야 합니다:
            1. 지원 동기
            2. 성격의 장단점
            3. 직무 역량
            4. 입사 후 포부

            각 항목을 구체적으로 작성해주세요 (총 3000자 내외).
            결과:""")
        self.cover_letter_refine = PromptTemplate.from_template(
            """
            [기존 자기소개서 내용]
            {previous_response}

            [사용자 수정 요청]
            {user_input}

            위 내용을 참고하여 수정해주세요.
            결과:""")
        self.interview_intent = PromptTemplate.from_template(
            """
            사용자의 입력을 분석하여 다음 중 하나를 출력하세요:
            - 인성 면접 (사용자 입력에 '인성' 포함)
            - 기술 면접 (사용자 입력에 '기술' 포함)
            - 종료 (사용자 입력에 '종료' 포함)
            - 관련 없음

            사용자 입력: {user_input}
            결과:""")
        self.interview_tenacity = PromptTemplate.from_template(
            """
            당신은 인성 면접관입니다. 다음 가이드라인에 따라 면접을 진행하세요:
            1. 답변 분석: 사용자의 이전 답변을 분석합니다.
            2. 후속 질문 생성: 답변과 자연스럽게 연결되는 질문을 생성합니다.
            3. 질문 스타일: 친근하고 자연스러운 어조로 질문합니다.

            예시 입력: "프로젝트 리더 경험이 있습니다."
            예시 출력: "프로젝트 리더 경험이 인상적이네요. 그렇다면 팀 내 갈등은 어떻게 해결하셨나요?"

            사용자 입력: {user_input}
            DB 내역: {interview_history}
            결과:""")
        self.interview_technology = PromptTemplate.from_template(
            """
            당신은 기술 면접관입니다. 다음 가이드라인에 따라 면접을 진행하세요:
            1. 답변 분석: 사용자의 기술적 이해도를 파악합니다.
            2. 후속 질문 생성: 심화 질문을 생성합니다.
            3. 질문 스타일: 전문적인 어조로 질문합니다.

            예시 입력: "저는 async/await를 사용합니다."
            예시 출력: "async/await에 대해 잘 알고 계시군요. 그렇다면 Promise와의 차이점은 무엇이라고 생각하시나요?"

            사용자 입력: {user_input}
            DB 내역: {interview_history}
            자기소개서: {cover_letter}
            결과:""")
    
    def create_and_save_customer_db(self):
        cursor = self.db.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS customer (
            customer_id VARCHAR(20) PRIMARY KEY
        )
        """
        cursor.execute(create_table_query)
        self.db.commit()
        cursor.execute("SELECT customer_id FROM customer")
        existing_users = set(row[0] for row in cursor.fetchall())
        users = User.objects.all()
        new_users = [user.username for user in users if user.username not in existing_users]
        if new_users:
            insert_query = "INSERT INTO customer (customer_id) VALUES (%s)"
            cursor.executemany(insert_query, [(user,) for user in new_users])
            self.db.commit()
        cursor.close()
    
    def create_saved_jobs_table(self):
        cursor = self.db.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS saved_job_posting (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id VARCHAR(20),
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
            마감일자 VARCHAR(255),
            foreign key(customer_id) references customer (customer_id)
        )
        """
        cursor.execute(create_table_query)
        cursor.execute("DELETE FROM saved_job_posting")
        cursor.execute("ALTER TABLE saved_job_posting AUTO_INCREMENT = 1")
        self.db.commit()
        cursor.close()
    
    def create_saved_cover_letter_table(self):
        cursor = self.db.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS saved_cover_letter (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id VARCHAR(20),
            자기소개서 TEXT,
            저장일시 DATETIME DEFAULT CONVERT_TZ(NOW(), 'UTC', 'Asia/Seoul'),
            foreign key(customer_id) references customer (customer_id)
        )
        """
        cursor.execute(create_table_query)
        self.db.commit()
        cursor.close()
    
    def create_saved_interview_question_table(self):
        cursor = self.db.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS saved_interview_question (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id VARCHAR(20),
            면접질문 TEXT,
            저장일시 DATETIME DEFAULT CONVERT_TZ(NOW(), 'UTC', 'Asia/Seoul'),
            foreign key(customer_id) references customer (customer_id)
        )
        """
        cursor.execute(create_table_query)
        cursor.execute("DELETE FROM saved_interview_question")
        self.db.commit()
        cursor.close()
    
    def classify_intent(self, state: State) -> State:
        intent = str(self.llm.invoke(self.intent_template.format(user_input=state["user_input"])).content).strip()
        print('user_id:', state['user_id'])
        if state["interview_in"] and state["intent_interview"]:
            intent = "INTERVIEW"
        if intent not in ["JOB_SEARCH", "COVER_LETTER", "INTERVIEW", "UNKNOWN"]:
            intent = "UNKNOWN"
        print(f"Classified intent: {intent}")
        return {**state, "intent": intent}
    
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
        return {**state, "job_results": result}
    
    def search_select_job(self, state: State) -> Dict:
        cursor = self.db.cursor()
        query = """
        SELECT 제목, 사용기술, 주요업무, 자격요건, 우대사항
        FROM saved_job_posting
        WHERE id = %s AND customer_id = %s
        """
        print(query)
        cursor.execute(query, (state['selected_job'], state['user_id'],))
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
    
    def search_cover_letter(self, state: State) -> State:
        cursor = self.db.cursor()
        query = """
        SELECT 자기소개서
        FROM saved_cover_letter
        WHERE customer_id = %s
        ORDER BY 저장일시 DESC
        LIMIT 1
        """
        cursor.execute(query, (state['user_id'],))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return {**state, "cover_letter": result[0]}
        return {**state, "cover_letter": None}
    
    def search_interview_question(self, state: State) -> State:
        try:
            cursor = self.db.cursor()
            query = """
            SELECT 면접질문
            FROM saved_interview_question
            WHERE customer_id = %s
            """
            cursor.execute(query, (state['user_id'],))
            result = cursor.fetchall()
            cursor.close()
            if not result:
                return {**state, "interview_q": []}
            questions = [row[0] for row in result]
            return {**state, "interview_q": questions}
        except Exception as e:
            print(f'에러 발생: {e}')
    
    def save_jobs_to_table(self, user_id, jobs):
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM saved_job_posting")
        self.db.commit()
        insert_query = """
        INSERT INTO saved_job_posting
        (customer_id, 제목, 회사명, 사용기술, 근무지역, 근로조건, 모집기간, 링크, 
         주요업무, 자격요건, 우대사항, 복지_및_혜택, 채용절차,
         학력, 근무지역_상세, 마감일자)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, 
                %s, %s, %s)
        """
        for job in jobs:
            cursor.execute(insert_query, (user_id, *job))
        self.db.commit()
        cursor.close()
    
    def save_cover_letter_to_table(self, user_id, cover_letter):
        cursor = self.db.cursor()
        query = """
        INSERT INTO saved_cover_letter (customer_id, 자기소개서)
        VALUES (%s, %s)
        """
        cursor.execute(query, (user_id, cover_letter))
        self.db.commit()
        cursor.close()
    
    def save_interview_question_to_table(self, user_id, interview_question):
        cursor = self.db.cursor()
        query = """
        INSERT INTO saved_interview_question (customer_id, 면접질문)
        VALUES (%s, %s)
        """
        cursor.execute(query, (user_id, interview_question))
        self.db.commit()
        cursor.close()
    
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
                if search_result.get("response") and search_result.get("response") == "검색할 직무 키워드를 입력해주세요.":
                    return search_result
                result = search_result.get("job_results", [])
                self.save_jobs_to_table(state['user_id'], result)
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
                        "상세 정보를 원하시면, 공고 번호와 함께 상세 정보라고 입력해주세요.\n"
                        "자기소개서 초안을 원하시면, 공고 번호와 자기소개서 작성을 입력해주세요.\n"
                        "면접 연습을 원하시면, 공고 번호와 면접 연습을 입력해주세요."
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
                extracted_info = "\n".join(f"{name}: {detail}" for name, detail in zip(moreinfo_list, result))
                response = str(self.llm.invoke(self.natural_response.format(extracted_info=extracted_info)).content).strip()
                return {**state, "response": response, "selected_job": num, "job_search": True}
            else:
                return {**state, "response": "선택하신 상세 정보가 없습니다."}
        elif search_road == "관련 없음":
            return {**state, "intent_search_job": "UNKNOWN"}
    
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
                    self.save_cover_letter_to_table(state['user_id'], cover_letter_writing)
                    response += cover_letter_writing
                    response += (
                        "\n\n추가 수정을 원하시면 수정 요청 사항을 입력해주세요."
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
                    self.save_cover_letter_to_table(state['user_id'], cover_letter_writing)
                    response += cover_letter_writing
                    response += (
                        "\n\n추가 수정을 원하시면 수정 요청 사항을 입력해주세요."
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
                return {**state, "response": "작성된 자기소개서가 없습니다. 먼저 작성해주세요."}
            refine_cover_letter = str(self.llm.invoke(
                self.cover_letter_refine.format(
                    user_input=state["user_input"],
                    previous_response=state["cover_letter"]
                )
            ).content).strip()
            self.save_cover_letter_to_table(state['user_id'], refine_cover_letter)
            response += refine_cover_letter
            response += (
                "\n\n추가 수정을 원하시면 수정 요청 사항을 입력해주세요."
            )
            return {**state, "response": refine_cover_letter, "cover_letter": refine_cover_letter}
        elif cl_road == "관련 없음":
            return {**state, "intent_cover_letter": "UNKNOWN"}
    
    def interview_chat(self, state: State) -> State:
        try:
            self.create_saved_interview_question_table()
            current_intent = state.get('intent_interview')
            if current_intent in ['TENACITY', 'TECHNOLOGY']:
                if "종료" in state["user_input"].lower():
                    return {**state, "response": "면접 연습을 종료합니다.", "intent_interview": "END", "interview_in": False}
                return {**state, "intent_interview": current_intent, "interview_in": True}
            interview_road = str(self.llm.invoke(
                self.interview_intent.format(user_input=state["user_input"])
            ).content).strip()
            print("면접 분기: ", interview_road)
            if interview_road == '인성 면접':
                return {**state, "intent_interview": "TENACITY", "interview_in": True}
            elif interview_road == '기술 면접':
                if not state.get('cover_letter_in'):
                    return {**state, "response": "기술 면접을 위해서는 먼저 자기소개서가 필요합니다.", "intent_interview": "END"}
                return {**state, "intent_interview": "TECHNOLOGY", "interview_in": True}
            elif interview_road == '종료':
                return {**state, "response": "면접 연습을 종료합니다.", "intent_interview": "END"}
            else:
                return {**state, "intent_interview": "UNKNOWN"}
        except Exception as e:
            print(f'에러 발생: {e}')
    
    def tenacity_interview(self, state: State) -> State:
        try:
            if state['interview_in']:
                self.create_saved_interview_question_table()
                search_result = self.search_interview_question(state)
                print("면접 질문 검색 완료")
            questions = search_result.get("interview_q", [])
            response_text = str(self.llm.invoke(
                self.interview_tenacity.format(
                    user_input=state['user_input'], 
                    interview_history=questions
                )
            ).content).strip()
            self.save_interview_question_to_table(state['user_id'], response_text)
            # TTS 파일 생성 대신 단순히 응답 텍스트 반환
            return {**state, "response": response_text, "intent_interview": "TENACITY", "interview_in": True}
        except Exception as e:
            print(f'에러 발생: {e}')
    
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
            response_text = str(self.llm.invoke(
                self.interview_technology.format(
                    user_input=state['user_input'], 
                    interview_history=questions, 
                    cover_letter=state['cover_letter']
                )
            ).content).strip()
            self.save_interview_question_to_table(state['user_id'], response_text)
            # TTS 파일 생성 대신 단순히 응답 텍스트 반환
            return {**state, "response": response_text, "intent_interview": "TECHNOLOGY", "interview_in": True}
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
    
def main():
    bot = JobAssistantBot()
    workflow = bot.create_workflow()
    bot.show_graph(workflow)
    print("Job Assistant Bot이 시작되었습니다. 종료하려면 'quit' 또는 'exit'를 입력하세요.")
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
        state["user_input"] = user_input
        try:
            result = workflow.invoke(state)
            state.update(result)
            print(state)
            if state.get("response"):
                print(f"Bot: {state['response']}")
            else:
                print("Bot: 죄송합니다. 처리 중 문제가 발생했습니다.")
        except Exception as e:
            print(f"오류가 발생했습니다: {str(e)}")
    
if __name__ == "__main__":
    main()
