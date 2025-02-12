from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .new_copy import JobAssistantBot

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
    "interview_q": [],
    "interview_in": False,
    "intent_interview": None
}

# JobAssistantBot 실행
bot = JobAssistantBot()
workflow = bot.create_workflow()
bot.show_graph(workflow)

@csrf_exempt
@require_http_methods(["POST"])
def chatbot_api(request):
    try:

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
        # print(state)

        return JsonResponse({"message": state.get("response", "죄송합니다. 처리 중 문제가 발생했습니다.")}, status=200)

    except Exception as e:
        return JsonResponse({"error": f"오류가 발생했습니다: {str(e)}"}, status=500)
