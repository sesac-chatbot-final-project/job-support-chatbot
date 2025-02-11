from django.db import models

class ChatMessage(models.Model):
    session_id = models.CharField(max_length=255)  # 세션 ID
    content = models.TextField()  # 메시지 내용
    is_user = models.BooleanField(default=True)  # 사용자인지 여부
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 날짜
