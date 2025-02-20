import jwt
import datetime
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from django.conf import settings

import os
import pymysql

from .hs import JobAssistantBot

JWT_SECRET = settings.JWT_SECRET
JWT_EXP_DELTA_SECONDS = settings.JWT_EXP_DELTA_SECONDS
JWT_ALGORITHM = "HS256"

# 각 요청마다 새 연결을 생성하는 헬퍼 함수
def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        charset="utf8mb4"
    )

# 챗봇 상태 초기값
INITIAL_STATE = {
    "user_id": "",
    "user_input": "",
    "chat_history": [],
    "intent": None,
    "intent_search_job": None,
    "job_name": "",
    "selected_job": None,
    "index_job": None,
    "job_search": False,
    "response": None,
    "job_results": [],
    "intent_cover_letter": None,
    "cover_letter": None,
    "cover_letter_in": False,
    "cover_letter_now": False,
    "interview_q": [],
    "interview_in": False,
    "intent_interview": None,
    "experience": None,
    "job_name": None
}

# JobAssistantBot 실행
bot = JobAssistantBot()
workflow = bot.create_workflow()
bot.show_graph(workflow)

def jwt_required(view_func):
    """
    JWT 토큰을 검증하는 데코레이터입니다.
    클라이언트는 Authorization 헤더에 "Bearer <토큰>" 형식으로 전달해야 합니다.
    """
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header:
            return JsonResponse({'error': '로그인 후 사용해 주세요.'}, status=401)
        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            request.user_payload = payload
        except IndexError:
            return JsonResponse({'error': '잘못된 인증 헤더 형식입니다.'}, status=401)
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': '토큰이 만료되었습니다.'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': '유효하지 않은 토큰입니다.'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def chatbot_api(request):
    try:
        state = request.session.get('state', None)
        if state is None:
            state = INITIAL_STATE.copy()
        state["user_id"] = request.user_payload["username"]

        if not request.body:
            return JsonResponse({"error": "요청 데이터가 없습니다."}, status=400)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "올바른 JSON 형식이 아닙니다."}, status=400)

        user_input = data.get("user_input", "").strip()
        if not user_input:
            return JsonResponse({"error": "메시지를 입력해주세요."}, status=400)

        state["user_input"] = user_input

        result = workflow.invoke(state)
        if result is None:
            return JsonResponse({"error": "워크플로우 실행 결과가 없습니다."}, status=500)
        print(result)
        state.update(result)

        request.session['state'] = state

        response_data = {
            "message": state.get("response", "죄송합니다. 처리 중 문제가 발생했습니다.")
        }
        return JsonResponse(response_data, status=200)
    except Exception as e:
        return JsonResponse({"error": f"오류가 발생했습니다: {str(e)}"}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def check_username(request):
    username = request.GET.get("username", "").strip()
    if not username:
        return JsonResponse({"error": "아이디를 입력해주세요."}, status=400)

    exists = User.objects.filter(username=username).exists()
    return JsonResponse({"exists": exists}, status=200)

@csrf_exempt
@require_http_methods(["POST"])
def register_user(request):
    try:
        if not request.body:
            return JsonResponse({"error": "요청 데이터가 없습니다."}, status=400)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "올바른 JSON 형식이 아닙니다."}, status=400)

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        if not username or not password:
            return JsonResponse({"error": "아이디와 비밀번호를 모두 입력해주세요."}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "이미 사용 중인 아이디입니다."}, status=400)

        user = User.objects.create(username=username, password=make_password(password))
        return JsonResponse({"message": "회원가입에 성공했습니다."}, status=201)
    except Exception as e:
        return JsonResponse({"error": f"회원가입 중 오류가 발생했습니다: {str(e)}"}, status=500)

def generate_jwt(user):
    payload = {
        "user_id": user.id,
        "username": user.username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    try:
        if not request.body:
            return JsonResponse({"error": "요청 데이터가 없습니다."}, status=400)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "올바른 JSON 형식이 아닙니다."}, status=400)

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        if not username or not password:
            return JsonResponse({"error": "아이디와 비밀번호를 모두 입력해주세요."}, status=400)

        user = authenticate(username=username, password=password)
        if user is not None:
            token = generate_jwt(user)
            userProfile = {
                "name": user.username,
                "email": user.email,
            }
            request.session['state'] = INITIAL_STATE.copy()
            return JsonResponse({
                "message": "로그인에 성공했습니다.",
                "token": token,
                "userProfile": userProfile
            }, status=200)
        else:
            return JsonResponse({"error": "아이디 또는 비밀번호가 올바르지 않습니다."}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"로그인 중 오류가 발생했습니다: {str(e)}"}, status=500)

# 새 엔드포인트: 로그인한 사용자의 자기소개서(자소서) 조회 (saved_cover_letter 테이블)
@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_resumes(request):
    username = request.user_payload["username"]
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = """
    SELECT 
        id,
        채용공고 AS title,
        자기소개서 AS content,
        DATE_FORMAT(저장일시, '%%Y-%%m-%%d') AS date
    FROM saved_cover_letter
    WHERE customer_id = %s
    """
    cursor.execute(query, (username,))
    resumes = cursor.fetchall()
    cursor.close()
    conn.close()
    return JsonResponse(resumes, safe=False)

# 새 엔드포인트: 로그인한 사용자의 면접 질문 조회 (personal_interview_question 테이블)
@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_interviews(request):
    username = request.user_payload["username"]
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = """
    SELECT 
        id, 
        면접질문 AS question, 
        DATE_FORMAT(저장일시, '%%Y-%%m-%%d') AS date
    FROM personal_interview_question
    WHERE customer_id = %s
    """
    cursor.execute(query, (username,))
    interviews = cursor.fetchall()
    cursor.close()
    conn.close()
    return JsonResponse(interviews, safe=False)

# 새 엔드포인트: 로그인한 사용자의 확인한 채용공고 조회 (selected_job_posting 테이블)
@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_job_postings(request):
    username = request.user_payload["username"]
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = """
    SELECT 
        id,
        제목,
        회사명,
        링크 AS link,
        DATE_FORMAT(저장일시, '%%Y-%%m-%%d') AS date
    FROM selected_job_posting
    WHERE customer_id = %s
    """
    cursor.execute(query, (username,))
    job_postings = cursor.fetchall()
    cursor.close()
    conn.close()
    return JsonResponse(job_postings, safe=False)
