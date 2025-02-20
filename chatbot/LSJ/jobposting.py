import pymysql
import os
from typing import Dict, TypedDict, Optional, List, Literal
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import graphviz
from langsmith import Client
from langsmith.run_trees import RunTree

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# langsmith
LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')

db = pymysql.connect(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT')),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    charset="utf8mb4"
)

class State(TypedDict):
    user_input: str  # 사용자 채팅 입력
    chat_history: List[Dict[str, str]]  # 대화 기록
    intent: Optional[str]  # 어떤 기능 사용할건지 저장
    intent_search_job: Optional[str]  # 공고 검색 기능에서의 분기
    job_name: str  # 직무 이름 / 채용 공고 기능에서 사용
    selected_job: int  # 선택한 공고
    job_search: bool  # 공고 선택 여부
    response: Optional[str]  # 챗봇 답변
    job_results: Optional[List[tuple]]  # 공고 질문 답변 출력 결과
    cover_letter: Optional[str]  # 작성한 자기소개서
    intent_cover_letter: Optional[str]  # 자기소개서 기능에서의 분기
    cover_letter_in: bool  # 자기소개서 DB 저장(작성) 여부

class JobAssistantBot:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o")
        self._initialize_prompts()
        self.create_saved_jobs_table()

    # prompt 모아두는 함수
    def _initialize_prompts(self):
        self.intent_template = PromptTemplate.from_template(
            """
            사용자 입력을 분석하여 다음 중 하나로 분류하여 결과로 출력하세요:
            - JOB_SEARCH
            : 직무를 입력하며 채용 공고를 탐색
            : 공고 번호를 입력하며 상세 정보를 요청
            - COVER_LETTER
            : 경험을 입력하며 자기소개서 작성을 요구
            : 자기소개서 수정을 요청
            - INTERVIEW
            : 면접 연습을 요청
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
            - 자기소개서 작성
            : 사용자가 공고를 활용해 자기소개서 작성을 원하는 경우
            - 면접 연습
            : 사용자가 공고를 활용해 면접 연습을 원하는 경우
            - 관련 없음
            : 채용 공고 탐색 기능과 관계 없는 입력

            상세 정보, 자기소개서 작성, 면접 연습의 경우 사용자가 입력한 공고 번호를 쉼표로 구분해 함께 리스트로 출력해주세요.
            채용 공고 제공과 관련 없음의 경우 -1을 리스트로 함께 출력해주세요.
            
            예시 입력: "첫 번째 공고 우대사항 알려줘"
            예시 출력: 상세 정보, 1

            예시 입력: "프론트엔드 개발자 공고 알려줘"
            예시 출력: 채용 공고 제공, -1

            예시 입력: "오늘 저녁 메뉴 추천해줘"
            예시 출력: 관련 없음, -1

            사용자 입력: {user_input}
            결과:""")

        self.jobname_prompt = PromptTemplate.from_template(
            # """
            # 사용자의 입력을 분석하여 직무가 포함되어 있는지 판단하세요:
            # - include
            # : 직무가 포함되어 있는 경우
            # - not_include
            # : 직무가 포함되어 있지 않는 경우

            # 예시 입력: "백엔드 개발자 공고 알려줘"
            # 예시 출력: include

            # 예시 입력: "공고 알려줘"
            # 예시 출력: not_include

            # 사용자 입력: {user_input}
            # 결과:""")
            """
            사용자의 입력을 분석하여 직무 관련 키워드가 포함되어 있는지 판단하세요:
            - include
            : '백엔드', '프론트엔드', '개발자', '프로그래머', 'AI', '인공지능', '데이터' 등 
              직무나 기술 스택 관련 키워드가 포함된 경우
            - not_include
            : 직무 관련 키워드가 전혀 포함되어 있지 않은 경우

            예시 입력: "백엔드 개발자 공고 알려줘"
            예시 출력: include

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
            결과를 쉼표로 구분된 키워드 리스트로만 반환해주세요.

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

            여러 가지 정보를 원했다면 결과를 쉼표로 구분된 키워드 리스트로만 반환해주세요.
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
            - 자기소개서 수정
            : 사용자가 자기소개서 수정을 요청하는 경우
            - 면접 연습
            : 사용자가 면접 연습을 요청하는 경우
            - 관련 없음
            : 자기소개서 기능과 관계 없는 입력

            예시 입력: AI 개발자 직무에 지원하려고 해
                       나는 LLM을 활용해서 챗봇을 개발하는 프로젝트를 진행했고, 그 프로젝트를 통해 LLM을 활용하는 방법을 배웠어.
                       이 경험을 활용해서 자기소개서 작성해줘
            예시 출력: 자기소개서 작성

            예시 입력: 직무 역량에서 A 프로젝트의 a 내용을 추가해줘
            예시 출력: 자기소개서 수정

            예시 입력: 모의 면접 부탁해
            예시 출력: 면접 연습

            사용자 입력: {user_input}
            결과:""")

        self.experience_prompt = PromptTemplate.from_template(
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
            각 항목 별로 공백을 포함하지 않고 500자에서 700자 사이로 작성해주세요.    
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

    # 분기점
    def classify_intent(self, state: State) -> State:
        intent = str(self.llm.invoke(self.intent_template.format(user_input=state["user_input"])).content).strip()
        return {**state, "intent": intent}

    # 저장된 공고를 위한 테이블 생성
    def create_saved_jobs_table(self):
        
        cursor = db.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS sj_saved (
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
        delete_data_query = "DELETE FROM sj_saved"
        cursor.execute(delete_data_query)
        
        # AUTO_INCREMENT 값 초기화
        reset_auto_increment_query = "ALTER TABLE sj_saved AUTO_INCREMENT = 1"
        cursor.execute(reset_auto_increment_query)

        db.commit()
        cursor.close()

    # 채용 공고 불러오기
    def search_job(self, state: State) -> State:
        cursor = db.cursor()
        search_keyword = str(self.llm.invoke(self.jobname_extract_prompt.format(user_input=state["user_input"])).content).strip()
        print(state["user_input"])
        print(search_keyword)
        search_keywords = [kw.strip() for kw in search_keyword.split(', ') if kw.strip()]
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
    
    # 검색된 공고들을 sj_saved 테이블에 저장
    def save_jobs_to_table(self, jobs):
        cursor = db.cursor()
        cursor.execute("DELETE FROM sj_saved")
        db.commit()

        insert_query = """
        INSERT INTO sj_saved
        (제목, 회사명, 사용기술, 근무지역, 근로조건, 모집기간, 링크, 
        주요업무, 자격요건, 우대사항, 복지_및_혜택, 채용절차,
        학력, 근무지역_상세, 마감일자)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, 
                %s, %s, %s)
        """

        for job in jobs:
            cursor.execute(insert_query, job)
        
        db.commit()
        cursor.close()

    # 채용 공고 제공 기능
    def search_job_chat(self, state: State) -> State:
        search_road, num = self.llm.invoke(self.search_job_prompt.format(user_input=state["user_input"])).content.split(',')
        num = int(num.strip())
        print('채용공고 분기', search_road, num)
        response = ""
        
        if search_road == "채용 공고 제공":
            jobname_validate = str(self.llm.invoke(self.jobname_prompt.format(user_input=state["user_input"])).content).strip()
            print(jobname_validate)
            if jobname_validate == "not_include":
                return {**state, "response": "탐색을 원하는 직무를 입력해주세요."}
            else:
                self.create_saved_jobs_table()
                search_result = self.search_job(state)
                
                # 에러 응답이 있는 경우 그대로 반환
                if search_result.get("response"):
                    return search_result
                
                # 검색 결과 가져오기
                result = search_result.get("job_results", [])
                self.save_jobs_to_table(result)
                
                if result:
                    for i, job in enumerate(result[:5], 1):
                        response += (
                            f"{i}.  {job[0]}\n"
                            f"  회사명: {job[1]}\n"
                            f"  기술스택: {job[2]}\n"
                            f"  근무지: {job[3]}\n"
                            f"  조건: {job[4]}\n"
                            f"  모집기간: {job[5]}\n"
                            f"  [지원 링크] ({job[6]})\n\n"
                        )
                    response += (
                        f"상세 정보 (주요 업무, 자격 요건, 우대사항, 복지 및 혜택, 채용절차, 학력, 근무지역 상세, 마감일자) 를 알고 싶으시면 키워드를 입력해주세요.\n"
                        f"모든 상세 정보를 알고 싶으시면 상세 정보라고 입력해주세요.\n"
                        f"공고를 선택해 맞춤형 자기소개서 초안을 작성하고 싶으시면 공고 번호와 자기소개서 키워드를 입력해주세요.\n"
                        f"공고를 선택해 맞춤형 면접 연습을 진행하고 싶으시면 공고 번호와 면접 키워드를 입력해주세요.\n"
                    )
                    return {**state, "response": response, "selected_job": num}
                else:
                    return {**state, "response": "관련된 채용 공고를 찾지 못했습니다."}

        elif search_road == "상세 정보":
            moreinfo = self.llm.invoke(self.moreinfo_extract_prompt.format(user_input=state["user_input"])).content
            moreinfo_list = moreinfo.split(',')
            field_name = ', '.join(mi.strip() for mi in moreinfo_list)
            moreinfo_query = f"""
            SELECT {field_name} FROM sj_saved
            ORDER BY id ASC
            LIMIT 1 OFFSET %s
            """

            cursor = db.cursor()
            cursor.execute(moreinfo_query, (num-1,))
            result = cursor.fetchone()
            cursor.close()
            if result:
                for name, detail in zip(moreinfo_list, result):
                    response += f"{name}:\n{detail}\n\n"
                return {**state, "response": response, "selected_job": num}
            else:
                return {**state, "response": "선택하신 상세 정보가 없습니다."} 


        
        elif search_road == "자기소개서":
            return {**state, "intent_search_job": "COVER_LETTER", "selected_job": num, "job_search": True}
        elif search_road == "면접 연습":
            return {**state, "intent_search_job": "INTERVIEW", "selected_job": num, "job_search": True}
        elif search_road == "관련 없음":
            return {**state, "intent_search_job": "UNKNOWN"}
    
    # 자기소개서 저장을 위한 테이블 생성
    def create_saved_cover_letter_table(self):
        cursor = db.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS saved_cover_letter (
            id INT AUTO_INCREMENT PRIMARY KEY,
            자기소개서 TEXT,
            저장일시 DATETIME DEFAULT CONVERT_TZ(NOW(), 'UTC', 'Asia/Seoul')
        )
        """

        cursor.execute(create_table_query)

        db.commit()
        cursor.close()
    
    # 지정한 공고 불러오기
    def search_select_job(self, state: State) -> State:
        cursor = db.cursor()

        name = ['제목', '사용기술', '주요업무', '자격요건', '우대사항']
        query = f"""
        SELECT 제목, 사용기술, 주요업무, 자격요건, 우대사항
        FROM sj_saved
        WHERE id = %s
        """
        response = ""

        cursor.execute(query, (state['selected_job'], ))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return {**state, "response": response}
        else:
            return {**state, "response": "공고를 선택하지 않았습니다."}
    
    # 가장 최근에 생성한 자기소개서 불러오기
    def search_cover_letter(self, state: State) -> State:
        cursor = db.cursor()
        query = f"""
        SELECT 자기소개서
        FROM saved_cover_letter
        ORDER BY DATETIME DESC
        LIMIT 1
        """

        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        return {**state, "cover_letter": result}
    
    def cover_letter_chat(self, state: State) -> State:
        cl_road = str(self.llm.invoke(self.cover_letter_prompt.format(user_input=state["user_input"])).content).strip()
        print('자기소개서 분기', cl_road)
        response = ""

        if cl_road == "자기소개서 작성":
            if state["job_search"]:
                job_exp = str(self.llm.invoke(self.experience_prompt.format(user_input=state["user_input"])).content).strip()
                if job_exp == 'all_include' or job_exp == 'experience_include':
                    job_list = self.search_select_job()
                    cover_letter_writing = str(self.llm.invoke(self.cover_letter_write.format(job_name=job_list[0], tech_stack=job_list[1], job_desc=job_list[2], requirements=job_list[3], preferences=job_list[4])).content).strip()
                    print(cover_letter_writing)
                elif job_exp == 'job_include':
                    return {**state, "response": "자기소개서에 반영할 경험을 입력해주세요."}
                elif job_exp == 'not_include':
                    return {**state, "response": "자기소개서 작성을 위해 직무와 경험을 입력해주세요."}
            else:
                job_exp = str(self.llm.invoke(self.experience_prompt.format(user_input=state["user_input"])).content).strip()
                if job_exp == 'all_include' or job_exp == 'experience_include':
                    job_list = self.search_select_job()
                    cover_letter_writing = str(self.llm.invoke(self.cover_letter_write.format(job_name=job_list[0], tech_stack=job_list[1], job_desc=job_list[2], requirements=job_list[3], preferences=job_list[4])).content).strip()
                    print(cover_letter_writing)
                elif job_exp == 'job_include':
                    return {**state, "response": "자기소개서에 반영할 경험을 입력해주세요."}
                elif job_exp == 'not_include':
                    return {**state, "response": "자기소개서 작성을 위해 직무와 경험을 입력해주세요."}
        # elif cl_road == "자기소개서 수정":
        
        elif cl_road == "면접 연습":
            return {**state, "intent_cover_letter": "INTERVIEW"}
        elif cl_road == "관련 없음":
            return {**state, "intent_cover_letter": "UNKNOWN"}

    
    def unknown_message(self, state: State) -> State:
        response = "시스템과 관련 없는 질문입니다. 다른 질문을 입력해주세요."
        return {**state, "response": response}

    def create_workflow(self) -> StateGraph:
        workflow = StateGraph(State)

        workflow.add_node("classify_intent", self.classify_intent)
        workflow.add_node("search_job_chat", self.search_job_chat)
        workflow.add_node("cover_letter_chat", self.cover_letter_chat)
        
        workflow.add_node("unknown_message", self.unknown_message)

        workflow.set_entry_point("classify_intent")

        workflow.add_conditional_edges(
            "classify_intent",
            lambda state: state['intent'],
            {
                "JOB_SEARCH": "search_job_chat",
                # "COVER_LETTER": "",
                # "INTERVIEW": "",
                "UNKNOWN": "unknown_message"
            }
        )

        # workflow.add_conditional_edges(
        #     "search_job_chat",
        #     lambda state: state['intent_search_job'],
        #     {
        #         "COVER_LETTER": "cover_letter_chat",
        #         # "INTERVIEW": ""
        #         "UNKNOWN": "unknown_message"
        #     }
        # )

        workflow.add_conditional_edges(
            "cover_letter_chat",
            lambda state: state['intent_cover_letter'],
            {
                # "INTERVIEW": "",
                "UNKNOWN": "unknown_message"
            }
        )

        workflow.add_edge("search_job_chat", END)
        workflow.add_edge("cover_letter_chat", END)

        workflow.add_edge("unknown_message", END)

        return workflow.compile()
    
    def show_graph(self, workflow):
        try:
            img_data = workflow.get_graph().draw_mermaid_png()
            with open("graph.png", "wb") as f:
                f.write(img_data)
            print("Graph saved as 'graph.png'")  
        except Exception as e:
            print(f"Error generating graph: {str(e)}", status=500)

def main():
    # 봇 인스턴스 생성
    bot = JobAssistantBot()
    workflow = bot.create_workflow()
    # print(dir(workflow))
    
    # 워크플로우 그래프 시각화
    bot.show_graph(workflow)
    
    print("Job Assistant Bot이 시작되었습니다. 종료하려면 'quit' 또는 'exit'를 입력하세요.")
    
    while True:
        user_input = input("\n사용자: ")
        
        if user_input.lower() in ['quit', 'exit']:
            print("챗봇을 종료합니다.")
            break
            
        # 초기 상태 설정
        initial_state = {
            "user_input": user_input,
            "chat_history": [],
            "intent": None,
            "job_name": "",
            "selected_job": None,
            "job_search": False,
            "response": None
        }
        
        try:
                result = workflow.invoke(initial_state)
                
                # 응답 출력
                if result.get("response"):
                    print(f"Bot: \n{result['response']}")
                else:
                    print("Bot: 죄송합니다. 처리 중 문제가 발생했습니다.")
                
        except Exception as e:
            print(f"오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    main()