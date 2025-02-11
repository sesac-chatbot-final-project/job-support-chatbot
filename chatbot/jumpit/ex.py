import os
import uuid
import time
import threading
import json
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

class ValidationResult(TypedDict):
    is_valid: bool
    missing_items: List[str]
    message: str

class Intent(TypedDict):
    primary: str
    secondary: Optional[str]
    confidence: float
    required_info: List[str]

class State(TypedDict):
    user_input: str
    session_id: str
    job_id: Optional[int]
    cover_letter: Optional[str]
    selected_job: Optional[Dict[str, str]]
    chat_history: List[Dict[str, str]]
    intent: Optional[Intent]
    error_message: Optional[str]
    validation_result: Optional[ValidationResult]
    previous_intent: Optional[Intent]

class JobAssistantBot:
    def __init__(self):
        self.llm = ChatOpenAI(model='gpt-4')
        
        # 의도 분류 템플릿 개선
        self.intent_template = PromptTemplate.from_template("""
        사용자의 입력을 분석하여 다음 정보를 JSON 형식으로 반환하세요:
        1. primary: 주요 의도 (JOB_SEARCH, COVER_LETTER_NEW, COVER_LETTER_MODIFY, INTERVIEW, UNKNOWN 중 하나)
        2. secondary: 부가 의도 (예: 특정 직무 검색, 특정 항목 수정 등)
        3. confidence: 분류 신뢰도 (0.0 ~ 1.0)
        4. required_info: 해당 의도 처리를 위해 필요한 정보 목록

        분석 시 다음을 고려하세요:
        - 이전 대화 맥락
        - 사용자가 명시적으로 언급한 키워드뿐만 아니라 문맥상 의도
        - 필요한 정보의 존재 여부

        사용자 입력: {user_input}
        이전 대화 기록: {chat_history}
        이전 의도: {previous_intent}
        
        JSON 응답:""")

        # 입력 검증 템플릿
        self.validation_template = PromptTemplate.from_template("""
        다음 의도와 입력에 대해 필수 정보가 충분히 포함되어 있는지 검증하세요:

        의도: {intent}
        사용자 입력: {user_input}
        
        각 의도별 필수 정보:
        - COVER_LETTER_NEW: 
          * 직무 이름
          * 직무 경험 (프로젝트, 업무 등)
          * 기술 스택
        - INTERVIEW: 
          * 자기소개서

        JSON 형식으로 응답:
        {
            "is_valid": true/false,
            "missing_items": ["없는 항목 리스트"],
            "message": "사용자에게 보여줄 메시지"
        }
        """)

        # 자기소개서 작성 템플릿
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

        # 자기소개서 작성 템플릿 (공고 없는 경우)
        self.cover_letter_without_job_template = PromptTemplate.from_template("""
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

        # 면접 질문 생성 템플릿
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

    def validate_input(self, state: State) -> State:
        """사용자 입력을 검증합니다."""
        intent = state.get("intent")
        if not intent or intent["primary"] == "UNKNOWN":
            return state

        validation_result = self.llm.invoke(
            self.validation_template.format(
                intent=intent,
                user_input=state["user_input"]
            )
        )
        
        try:
            validation_data = json.loads(validation_result.content)
            return {**state, "validation_result": validation_data}
        except Exception as e:
            print(f"Validation error: {e}")
            return {**state, "error_message": "입력 검증 중 오류가 발생했습니다."}

    def classify_intent(self, state: State) -> State:
        """향상된 의도 분류"""
        try:
            previous_intent = state.get("previous_intent", None)
            
            response = self.llm.invoke(
                self.intent_template.format(
                    user_input=state["user_input"],
                    chat_history=state.get("chat_history", []),
                    previous_intent=previous_intent
                )
            )
            
            intent_data = json.loads(response.content)
            
            # 이전 의도가 있고, 현재 입력이 이전 의도의 필수 정보를 제공하는 경우
            if previous_intent and "validation_result" in state:
                prev_validation = state["validation_result"]
                if not prev_validation["is_valid"]:
                    # 이전에 요청했던 정보를 제공하는 경우, 이전 의도를 유지
                    return {**state, "intent": previous_intent}
            
            return {**state, 
                   "intent": intent_data,
                   "previous_intent": state.get("intent")}
            
        except Exception as e:
            print(f"Intent classification error: {e}")
            return {**state, "error_message": "의도 분류 중 오류가 발생했습니다."}

    def handle_job_search(self, state: State) -> State:
        """채용공고 검색을 처리합니다."""
        # 채용공고 검색 로직 구현
        return state

    def handle_cover_letter(self, state: State) -> State:
        """자기소개서 작성/수정을 처리합니다."""
        try:
            if state.get("validation_result") and not state["validation_result"]["is_valid"]:
                return state
            
            if state["intent"]["primary"] == "COVER_LETTER_NEW":  # 수정된 부분
                try:
                    job_data = Choice.objects.latest('datetime')
                    
                    prompt = self.cover_letter_template.format(  # 수정된 부분
                        job_name=job_data.name,
                        tech_stack=", ".join(job_data.stack),
                        job_desc=", ".join(job_data.work),
                        requirements=", ".join(job_data.need),
                        preferences=", ".join(job_data.good),
                        user_input=state["user_input"]
                    )
                except ObjectDoesNotExist:
                    prompt = self.cover_letter_without_job_template.format(
                        user_input=state["user_input"]
                    )

                cover_letter = str(self.llm.invoke(prompt).content)
                
                with transaction.atomic():
                    CoverLetter.objects.filter(session_id=state["session_id"]).delete()
                    CoverLetter.objects.create(
                        session_id=state["session_id"],
                        job=job_data,
                        content=cover_letter
                    )

                return {**state, "cover_letter": cover_letter}

            elif state["intent"]["primary"] == "COVER_LETTER_MODIFY":
                # 기존 자기소개서 수정
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

        except Exception as e:
            print(f"Error in handling cover letter: {e}")
            return state

    def handle_interview(self, state: State) -> State:
        """면접 연습을 처리합니다."""
        if state.get("requires_cover_letter"):
            return state

        try:
            # 자기소개서 가져오기
            if CoverLetter.objects.get(session_id=state["session_id"]).exists():
                cover_letter = CoverLetter.objects.get(session_id=state["session_id"])
                reference_text = cover_letter.content
            else:
                reference_text = state["user_input"]
            
            conversation_history = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in state.get("chat_history", [])
            ])

            # 면접 질문 생성
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
        """향상된 워크플로우"""
        workflow = StateGraph(State)
        
        workflow.add_node("classify_intent", self.classify_intent)
        workflow.add_node("validate_input", self.validate_input)
        workflow.add_node("handle_job_search", self.handle_job_search)
        workflow.add_node("handle_cover_letter", self.handle_cover_letter)
        workflow.add_node("handle_interview", self.handle_interview)
        
        workflow.set_entry_point("classify_intent")
        
        # 의도 분류 후 항상 검증 단계로
        workflow.add_edge("classify_intent", "validate_input")
        
        # 검증 결과에 따른 조건부 라우팅
        def route_by_validation(state: State) -> str:
            if state.get("error_message"):
                return "ERROR"
                
            validation_result = state.get("validation_result")
            if validation_result and not validation_result["is_valid"]:
                return "INVALID"
                
            intent = state.get("intent")
            return intent["primary"] if intent else "UNKNOWN"
        
        workflow.add_conditional_edges(
            "validate_input",
            route_by_validation,
            {
                "JOB_SEARCH": "handle_job_search",
                "COVER_LETTER_NEW": "handle_cover_letter",
                "COVER_LETTER_MODIFY": "handle_cover_letter",
                "INTERVIEW": "handle_interview",
                "UNKNOWN": END,
                "ERROR": END,
                "INVALID": END  # 검증 실패 시 에러 메시지와 함께 종료
            }
        )
        
        workflow.add_edge("handle_job_search", END)
        workflow.add_edge("handle_cover_letter", END)
        workflow.add_edge("handle_interview", END)
        
        return workflow.compile()

    def process_message(self, message: str, session_id: str) -> Dict:
        """메시지 처리 및 응답 생성"""
        workflow = self.create_workflow()
        
        try:
            # DB에서 대화 기록 가져오기
            chat_history = []  # DB 조회 로직 구현 필요
            
            initial_state = {
                "user_input": message,
                "session_id": session_id,
                "chat_history": chat_history,
                "intent": None,
                "previous_intent": None,
                "validation_result": None
            }
            
            final_state = workflow.invoke(initial_state)
            
            # 검증 실패 시
            if final_state.get("validation_result") and not final_state["validation_result"]["is_valid"]:
                return {
                    "type": "validation_error",
                    "message": final_state["validation_result"]["message"],
                    "missing_items": final_state["validation_result"]["missing_items"],
                    "previous_intent": final_state.get("previous_intent")
                }
            
            # 에러 발생 시
            if final_state.get("error_message"):
                return {
                    "type": "error",
                    "message": final_state["error_message"]
                }
            
            # 정상 응답
            response_content = None
            if final_state.get("cover_letter"):
                response_content = final_state["cover_letter"]
            elif final_state.get("chat_history"):
                # 가장 최근의 대화 내용 반환
                response_content = final_state["chat_history"][-2:]  # 질문과 답변 페어
                
            return {
                "type": "response",
                "content": response_content,
                "intent": final_state.get("intent")
            }
            
        except Exception as e:
            print(f"Error in process_message: {e}")
            return {
                "type": "error",
                "message": "메시지 처리 중 오류가 발생했습니다."
            }