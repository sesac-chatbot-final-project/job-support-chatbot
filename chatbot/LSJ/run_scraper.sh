# 한국시간(KST)으로 설정
export TZ='Asia/Seoul'

echo "=== Script Started ===" >> /home/ubuntu/job-search-support-chatbot/chatbot/LSJ/crawling.log
echo "$(date '+%Y-%m-%d %H:%M:%S') ===" >> /home/ubuntu/job-search-support-chatbot/chatbot/LSJ/crawling.log

# 가상환경 활성화
source /home/ubuntu/job-search-support-chatbot/sesac/bin/activate

# 크롤링 실행
/home/ubuntu/job-search-support-chatbot/sesac/bin/python /home/ubuntu/job-search-support-chatbot/chatbot/LSJ/crawling.py > /home/ubuntu/job-search-support-chatbot/chatbot/LSJ/crawling.log 2>&1

# 로그 끝날 때 한국시간으로 기록
echo "=== Script Ended ===" >> /home/ubuntu/job-search-support-chatbot/chatbot/LSJ/crawling.log
echo "$(date '+%Y-%m-%d %H:%M:%S')" >> /home/ubuntu/job-search-support-chatbot/chatbot/LSJ/crawling.log