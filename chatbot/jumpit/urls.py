from django.urls import path
from .views import (
    chatbot_api,
    check_username,
    register_user,
    login_user,
    get_resumes,
    get_interviews,
    get_job_postings
)

urlpatterns = [
    path("chat/", chatbot_api, name="chatbot_api"),  # 기존 챗봇 API
    path("users/check_username/", check_username, name="check_username"),
    path("users/register/", register_user, name="register_user"),
    path("users/login/", login_user, name="login_user"),
    # 새로 추가된 엔드포인트
    path("resumes/", get_resumes, name="get_resumes"),
    path("interviews/", get_interviews, name="get_interviews"),
    path("job-postings/", get_job_postings, name="get_job_postings"),
]
