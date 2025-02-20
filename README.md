# JOBARA : 취업 지원 서비스 Chatbot

## WINDOW에서 실행하는 방법

1.  git clone
    `git clone -b ec2 https://github.com/sesac-chatbot-final-project/job-support-chatbot.git`

2.  파이썬 설치

- https://www.python.org/downloads/windows/ 사이트에서 파이썬 3.9.12 버전 설치

3. job-support-chatbot 디렉토리로 이동
   `cd job-support-chatbot`

4. 가상환경 설치 및 실행
   `py -3.9 -m venv sesac`
   `sesac\Scripts\activate`

5. requirements.txt 설치
   `pip install -r requirements.txt`

6. 루트 디렉토리에 .env 파일 생성

- 별도 전달된 env 파일 사용
- OPENAI API KEY, DB, JWT KEY

7. node module 설치
   `cd front`
   `npm install`
   `npm install front --save-dev`

8. React & Django 시작

- front 디렉토리에서 npm start
- job-support-chatbot/chatbot 디렉토리로 이동 후 python manage.py runserver
