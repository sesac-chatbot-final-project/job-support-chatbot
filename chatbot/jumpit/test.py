import os
import uuid
import time
import threading
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wavfile
import boto3
import whisper
import pygame
from typing import Dict, TypedDict, Optional, List
from enum import Enum
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from models import Job, CoverLetter, Choice

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# AWS Polly 클라이언트 설정
polly_client = boto3.client(
    "polly",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

# Whisper 모델 설정
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "medium")
whisper_model = None

class ConversationIntent(Enum):
    JOB_SEARCH = "JOB_SEARCH"
    COVER_LETTER_NEW = "COVER_LETTER_NEW"
    COVER_LETTER_MODIFY = "COVER_LETTER_MODIFY"
    INTERVIEW = "INTERVIEW"
    UNKNOWN = "UNKNOWN"

class State(TypedDict):
    user_input: str
    session_id: str
    job_id: Optional[int]
    cover_letter: Optional[str]
    selected_job: Optional[Dict[str, str]]
    chat_history: List[Dict[str, str]]
    intent: Optional[str]
    error_message: Optional[str]
    requires_experience: bool
    requires_cover_letter: bool
    requires_position: bool
    position: Optional[str]

def load_whisper_model():
    """Whisper 모델 로드 함수"""
    global whisper_model
    print(f"Whisper {WHISPER_MODEL_SIZE} 모델 로딩 중...")
    whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
    print("모델 로딩 완료!")

def text_to_speech_polly(text, voice_id="Seoyeon"):
    """AWS Polly를 사용하여 텍스트를 음성으로 변환 후 재생"""
    try:
        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId=voice_id,
            Engine="neural",
        )

        filename = f"polly_tts_{uuid.uuid4()}.mp3"
        with open(filename, "wb") as f:
            f.write(response["AudioStream"].read())

        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.quit()
        os.remove(filename)

    except Exception as e:
        print("AWS Polly TTS 오류:", e)

def record_audio(filename="output.wav", duration=10, rate=44100):
    """향상된 음성 녹음 함수"""
    print("녹음 중... 답변이 끝나면 Enter를 눌러 종료하세요.")

    recording = []
    is_recording = True

    def callback(indata, frames, time, status):
        if is_recording and status:
            print("Error:", status)
        if is_recording:
            recording.append(indata.copy())

    def stop_recording():
        nonlocal is_recording
        input()
        is_recording = False

    stream = sd.InputStream(
        callback=callback,
        channels=1,
        samplerate=rate,
        dtype=np.int16,
        blocksize=4096,
        latency="low",
    )

    with stream:
        threading.Thread(target=stop_recording, daemon=True).start()
        while is_recording and len(recording) < (rate * duration) // 1024:
            sd.sleep(100)

    if not recording:
        return False

    try:
        recording = np.concatenate(recording)
        if len(recording) > 0:
            wavfile.write(filename, rate, recording)
            print(f"녹음 완료: {filename}")
            return True
        else:
            print("녹음 데이터가 없습니다.")
            return False

    except Exception as e:
        print(f"녹음 처리 중 오류 발생: {e}")
        return False

def recognize_audio_with_whisper(filename="output.wav"):
    """로컬 Whisper 모델을 사용한 음성 인식 함수"""
    try:
        global whisper_model
        if whisper_model is None:
            load_whisper_model()

        result = whisper_model.transcribe(filename, language="ko", task="transcribe")
        transcript = result["text"].strip()
        print("인식된 텍스트:", transcript)
        return transcript

    except Exception as e:
        print(f"Whisper 인식 오류: {e}")
        return ""

class JobAssistantBot:
    def __init__(self):
        self.llm = ChatOpenAI(model='gpt-4')
        
        # 메인 의도 분류 템플릿
        self.intent_template = PromptTemplate.from_template("""
        사용자의 입력을 다음 중 하나로 분류하세요:
        1. JOB_SEARCH: 채용공고 검색/조회 관련 입력
        2. COVER_LETTER_NEW: 새로운 자기소개서 작성 요청이나 경험/역량 설명
        3. COVER_LETTER_MODIFY: 기존 자기소개서 수정 요청
        4. INTERVIEW: 면접 연습 요청
        5. UNKNOWN: 위 경우에 해당하지 않는 입력

        사용자 입력: {user_input}
        이전 대화 기록: {chat_history}
        
        분류:""")

        # 자기소개서 작성 템플릿들은 그대로 유지
        self.cover_letter_template = PromptTemplate.from_template("""
        [채용 공고 정보]
        - 공고 이름: {job_name}
        - 기술 스택: {tech_stack}
        - 주요 업무: {job_desc}
        - 자격 요건: {requirements}
        - 우대 사항: {preferences}

        [사용자 경험]
        {user_input}

        자기소개서는 다음 4가지 항목을 포함해야 합니다:
        1. 지원 동기
        2. 성격의 장단점
        3. 직무 역량
        4. 입사 후 포부

        각 항목을 구체적으로 작성하세요. 
        각 항목 당 공백 불포함 500자에서 700자 사이로 작성해주세요.       
        """)

        self.cover_letter_without_job_template = PromptTemplate.from_template("""
        [지원 직무]
        {position}

        [사용자 경험]
        {user_input}

        자기소개서는 다음 4가지 항목을 포함해야 합니다:
        1. 지원 동기 (사용자의 경험과 관심 분야를 바탕으로)
        2. 성격의 장단점
        3. 직무 역량 (사용자의 기술적 경험을 중심으로)
        4. 입사 후 포부

        각 항목을 구체적으로 작성하세요. 
        각 항목 당 공백 불포함 500자에서 700자 사이로 작성해주세요.       
        """)

        self.cover_letter_modify_template = PromptTemplate.from_template("""
        다음은 기존의 자기소개서 초안입니다:
        {previous_response}

        사용자의 수정 요청:
        {user_input}

        위 수정 요청을 반영하여 자기소개서를 수정해주세요. 
        기존 내용의 일관성을 유지하면서 자연스럽게 수정사항을 반영해주세요.
        """)

        self.interview_template = PromptTemplate(
            input_variables=["reference_text", "conversation_history"],
            template="""
            너는 경력과 전문성을 갖춘 면접관이다. 
            지원자의 자소서나 채용공고 데이터를 참고하여, 적절한 면접 질문을 해주고, 
            사용자의 답변에 기반하여 추가 질문이나 피드백을 제공한다.
            질문은 구체적이고 명확하게 하되, 하나의 질문만 작성한다.

            참고 데이터:
            {reference_text}

            지금까지의 대화 이력:
            {conversation_history}

            면접 질문:"""
        )

    def validate_requirements(self, state: State) -> Optional[str]:
        """입력 요구사항을 검증하고 에러 메시지를 반환합니다."""
        intent = state.get("intent")
        
        if intent == "COVER_LETTER_NEW":
            if not state.get("position"):
                return "지원하고자 하는 직무를 입력해주세요."
            if not state.get("user_input") or len(state.get("user_input", "")) < 50:
                return "자기소개서 작성을 위해 본인의 경험을 상세히 입력해주세요."
                
        elif intent == "INTERVIEW":
            # 자기소개서 존재 여부 확인
            has_db_letter = False
            try:
                has_db_letter = CoverLetter.objects.filter(session_id=state["session_id"]).exists()
            except:
                pass
                
            has_text_letter = bool(state.get("user_input") and len(state.get("user_input")) > 300)
            
            if not (has_db_letter or has_text_letter):
                return "면접 연습을 위해서는 자기소개서가 필요합니다. 자기소개서를 입력하거나 작성해주세요."
        
        return None

    def check_requirements(self, state: State) -> State:
        """사용자 입력의 필수 요구사항을 확인합니다."""
        error_msg = self.validate_requirements(state)
        if error_msg:
            return {
                **state,
                "error_message": error_msg,
                "requires_experience": "경험" in error_msg,
                "requires_position": "직무" in error_msg,
                "requires_cover_letter": "자기소개서" in error_msg
            }
        return state

    def classify_intent(self, state: State) -> State:
        """사용자 입력의 의도를 분류합니다."""
        prompt = self.intent_template.format(
            user_input=state["user_input"],
            chat_history=state.get("chat_history", [])
        )
        intent = str(self.llm.invoke(prompt).content).strip()
        return {**state, "intent": intent}

    def handle_cover_letter(self, state: State) -> State:
        """자기소개서 작성/수정을 처리합니다."""
        try:
            if state.get("requires_experience") or state.get("requires_position"):
                return state
            
            if state["intent"] == "COVER_LETTER_NEW":
                # 새 자기소개서 작성
                try:
                    # 선택된 채용공고가 있는 경우
                    job_data = Choice.objects.filter(session_id=state["session_id"]).latest('datetime')
                    
                    prompt = self.cover_letter_template.format(
                        job_name=job_data.name,
                        tech_stack=", ".join(job_data.stack),
                        job_desc=", ".join(job_data.work),
                        requirements=", ".join(job_data.need),
                        preferences=", ".join(job_data.good),
                        user_input=state["user_input"]
                    )
                except ObjectDoesNotExist:
                    # 공고 없이 자기소개서 작성
                    prompt = self.cover_letter_without_job_template.format(
                        position=state.get("position", ""),
                        user_input=state["user_input"]
                    )

                cover_letter = str(self.llm.invoke(prompt).content)
                
                with transaction.atomic():
                    CoverLetter.objects.filter(session_id=state["session_id"]).delete()
                    CoverLetter.objects.create(
                        session_id=state["session_id"],
                        content=cover_letter
                    )

                return {**state, "cover_letter": cover_letter}

            elif state["intent"] == "COVER_LETTER_MODIFY":
                # 기존 자기소개서 수정
                try:
                    previous_letter = CoverLetter.objects.get(
                        session_id=state["session_id"]
                    ).content

                    prompt = self.cover_letter_modify_template.format(
                        previous_response=previous_letter,
                        user_input=state["user_input"]
                    )

                    modified_letter = str(self.llm.invoke(prompt).content)
                    
                    with transaction.atomic():
                        cover_letter_obj = CoverLetter.objects.get(session_id=state["session_id"])
                        cover_letter_obj.content = modified_letter
                        cover_letter_obj.save()

                    return {**state, "cover_letter": modified_letter}
                except ObjectDoesNotExist:
                    return {**state, "error_message": "수정할 자기소개서를 찾을 수 없습니다."}

        except Exception as e:
            print(f"Error in handling cover letter: {e}")
            return {**state, "error_message": f"자기소개서 처리 중 오류가 발생했습니다: {str(e)}"}

    def handle_interview(self, state: State) -> State:
        """면접 연습을 처리합니다."""
        if state.get("requires_cover_letter"):
            return state

        try:
            # 참조할 데이터 준비
            reference_text = ""
            
            # 1. 자기소개서 가져오기
            has_db_letter = False
            try:
                cover_letter = CoverLetter.objects.get(session_id=state["session_id"])
                reference_text += f"\n[자기소개서]\n{cover_letter.content}"
                has_db_letter = True
            except ObjectDoesNotExist:
                if state["user_input"] and len(state["user_input"]) > 300:
                    reference_text += f"\n[자기소개서]\n{state['user_input']}"
                    
            # 2. 채용공고 정보 가져오기 (있는 경우)
            try:
                job_data = Choice.objects.filter(session_id=state["session_id"]).latest('datetime')
                reference_text += f"\n[채용공고]\n"
                reference_text += f"직무: {job_data.name}\n"
                reference_text += f"기술스택: {', '.join(job_data.stack)}\n"
                reference_text += f"주요업무: {', '.join(job_data.work)}\n"
                reference_text += f"자격요건: {', '.join(job_data.need)}\n"
            except ObjectDoesNotExist:
                pass

            # 면접 질문 생성
            conversation_history = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in state.get("chat_history", [])
            ])

            question = str(self.llm.invoke(self.interview_template.format(
                reference_text=reference_text,
                conversation_history=conversation_history
            )).content)

            # 음성으로 질문하기
            text_to_speech_polly(question)

            # 음성 답변 받기
            if not record_audio(duration=30):
                return {**state, "error_message": "녹음에 실패했습니다. 다시 시도해주세요."}

            # 답변 텍스트 변환
            answer_text = recognize_audio_with_whisper()
            if not answer_text:
                return {**state, "error_message": "음성 인식에 실패했습니다. 다시 시도해주세요."}

            # 대화 기록 업데이트
            new_history = state.get("chat_history", []) + [
                {"role": "면접관", "content": question},
                {"role": "지원자", "content": answer_text}
            ]

            return {**state, "chat_history": new_history}

        except Exception as e:
            print(f"Error in interview: {e}")
            return {**state, "error_message": f"면접 진행 중 오류가 발생했습니다: {str(e)}"}

    def create_workflow(self) -> StateGraph:
        """워크플로우를 생성합니다."""
        workflow = StateGraph(State)
        
        # 노드 추가
        workflow.add_node("classify_intent", self.classify_intent)
        workflow.add_node("check_requirements", self.check_requirements)
        workflow.add_node("handle_job_search", self.handle_job_search)
        workflow.add_node("handle_cover_letter", self.handle_cover_letter)
        workflow.add_node("handle_interview", self.handle_interview)
        
        workflow.set_entry_point("classify_intent")

        # 기본 플로우: 의도 분류 -> 요구사항 체크
        workflow.add_edge("classify_intent", "check_requirements")
        
        # 요구사항 체크 후 조건부 라우팅
        def route_after_requirements(state: State):
            if state.get("error_message"):
                return END
            return state["intent"]
        
        workflow.add_conditional_edges(
            "check_requirements",
            route_after_requirements,
            {
                "JOB_SEARCH": "handle_job_search",
                "COVER_LETTER_NEW": "handle_cover_letter",
                "COVER_LETTER_MODIFY": "handle_cover_letter",
                "INTERVIEW": "handle_interview",
                "UNKNOWN": END
            }
        )
        
        # 각 핸들러에서 종료로 가는 엣지 추가
        workflow.add_edge("handle_job_search", END)
        workflow.add_edge("handle_cover_letter", END)
        workflow.add_edge("handle_interview", END)
        
        return workflow.compile()

def start_session() -> str:
    """새 세션을 시작하고 세션 ID를 반환합니다."""
    return str(uuid.uuid4())