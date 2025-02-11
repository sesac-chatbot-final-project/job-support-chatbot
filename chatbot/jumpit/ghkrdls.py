import os
import time
import threading
import numpy as np
import uuid
import boto3
import pygame
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일 로드
load_dotenv()

# AWS EC2 환경 감지
IS_EC2 = os.path.exists("/sys/hypervisor/uuid") and open("/sys/hypervisor/uuid").read().startswith("ec2")

# OpenAI 클라이언트 설정
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client.api_key:
    raise ValueError("OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

# AWS Polly 클라이언트 설정
polly_client = boto3.client(
    "polly",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

def text_to_speech_polly(text, voice_id="Seoyeon"):
    """AWS Polly를 사용하여 텍스트를 음성으로 변환 후 재생"""
    if IS_EC2:
        print(f"[AWS Polly 대체 출력] {text}")
        return

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
    """향상된 음성 녹음 함수 (EC2에서는 녹음 비활성화)"""
    if IS_EC2:
        print("[EC2 환경 감지] 녹음 기능을 비활성화합니다.")
        return False

    try:
        import sounddevice as sd
        import scipy.io.wavfile as wavfile

        print("녹음 중... 답변이 끝나면 Enter를 눌러 종료하세요.")
        recording = []
        is_recording = True

        def callback(indata, frames, time, status):
            if is_recording and status:
                print('Error:', status)
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
            latency='low'
        )

        with stream:
            threading.Thread(target=stop_recording, daemon=True).start()
            while is_recording and len(recording) < (rate * duration) // 1024:
                sd.sleep(100)

        if not recording:
            return False

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
    """Whisper API를 사용한 향상된 음성 인식 함수"""
    if IS_EC2:
        print("[EC2 환경 감지] 음성 인식을 비활성화합니다.")
        return ""

    try:
        with open(filename, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ko",
                response_format="text"
            )
        print("인식된 텍스트:", transcript)
        return transcript
    except Exception as e:
        print(f"Whisper API 오류: {e}")
        return ""

def generate_interview_question(reference_text, conversation_history):
    """면접 질문 생성 함수"""
    try:
        system_prompt = """너는 경력과 전문성을 갖춘 면접관이다.
            지원자의 자소서나 채용공고 데이터를 참고하여, 적절한 면접 질문을 해주고,
            사용자의 답변에 기반하여 추가 질문이나 피드백을 제공한다.
            질문은 구체적이고 명확하게 하되, 답변하기 쉽도록 간단히 해라."""

        user_prompt = (
            "아래 데이터를 참고하여 면접 질문을 해주세요.\n\n"
            "참고 데이터:\n"
            f"{reference_text}\n\n"
            "지금까지의 대화 이력:\n"
            f"{conversation_history}\n\n"
            "면접 질문:"
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=200,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API 오류: {e}")
        return "죄송합니다. 질문을 생성하는 데 문제가 발생했습니다."

def get_reference_text_from_db():
    """참고 데이터 로드 함수"""
    reference_text = """
    프론트엔드 개발자로 3년 경력.
    Vue.js와 React를 사용하여 웹 애플리케이션 개발 경험이 있으며,
    TypeScript와 Tailwind CSS를 활용한 UI 최적화 작업을 수행함.
    주요 프로젝트:
    - 대규모 전자상거래 플랫폼 리뉴얼 (React + TypeScript)
    - 실시간 데이터 시각화 대시보드 개발 (Vue.js)
    - 마이크로프론트엔드 아키텍처 설계 및 구현
    """
    return reference_text

def main():
    print("=== 음성 면접 챗봇 (Whisper 강화 버전) ===")
    print("DB에서 참고 데이터를 가져오는 중...")
    reference_text = get_reference_text_from_db()
    print(f"참고 데이터: {reference_text}\n")

    conversation_history = ""
    retry_count = 0
    max_retries = 3

    while True:
        try:
            question = generate_interview_question(reference_text, conversation_history)
            print("\n[면접관]:", question)
            text_to_speech_polly(question)

            if not record_audio(duration=30):
                print("녹음에 실패했습니다. 다시 시도해주세요.")
                continue

            answer_text = recognize_audio_with_whisper()
            if not answer_text:
                retry_count += 1
                if retry_count >= max_retries:
                    print("여러 번 인식에 실패했습니다. 다음 질문으로 넘어갑니다.")
                    retry_count = 0
                    continue
                print("다시 한 번 말씀해 주시겠습니까?")
                continue

            retry_count = 0
            if "면접 종료" in answer_text.lower():
                text_to_speech_polly("면접을 종료합니다. 수고하셨습니다.")
                break

            print("[지원자]:", answer_text)
            conversation_history += f"면접관: {question}\n지원자: {answer_text}\n"

        except Exception as e:
            print(f"오류 발생: {e}")
            print("프로그램을 다시 시작합니다...")
            time.sleep(2)

if __name__ == "__main__":
    main()