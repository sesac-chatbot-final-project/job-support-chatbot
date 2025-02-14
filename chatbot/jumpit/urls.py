from django.urls import path
from .views import chatbot_api, check_username, register_user, login_user

urlpatterns = [
    path('chat/', chatbot_api, name='chatbot_api'),  # 기존 Chatbot API URL
    path('users/check_username/', check_username, name='check_username'),  # 아이디 중복 확인 API
    path('users/register/', register_user, name='register_user'),  # 회원가입 API
    path('users/login/', login_user, name='login_user'),  # 로그인 API 엔드포인트 추가
]