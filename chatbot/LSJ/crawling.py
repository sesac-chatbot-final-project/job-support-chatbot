import os
import re
import time
import pymysql
import requests
from dotenv import load_dotenv
import pandas as pd
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import pytz

# 한국 시간 설정
KST = pytz.timezone("Asia/Seoul")

load_dotenv()

# MariaDB 연결 설정
db = pymysql.connect(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT')),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    charset="utf8mb4"
)

def create_saved_jobs_table():
    """저장된 공고 테이블 생성 및 초기화"""
    cursor = db.cursor()

    cursor.execute("DROP TABLE IF EXISTS job_posting_new")
    
    create_table_query = """
    CREATE TABLE job_posting_new (
        id INT AUTO_INCREMENT PRIMARY KEY,
        제목 VARCHAR(255),
        회사명 VARCHAR(255),
        사용기술 TEXT,
        근무지역 VARCHAR(255),
        근로조건 VARCHAR(255),
        모집기간 VARCHAR(255),
        링크 TEXT,
        저장일시 DATETIME DEFAULT CONVERT_TZ(NOW(), 'UTC', 'Asia/Seoul'),
        주요업무 TEXT,
        자격요건 TEXT,
        우대사항 TEXT,
        복지_및_혜택 TEXT,
        채용절차 TEXT,
        학력 VARCHAR(255),
        근무지역_상세 VARCHAR(255),
        마감일자 VARCHAR(255)
    )
    """
    cursor.execute(create_table_query)
    db.commit()
    cursor.close()

# 🔹 영어 → 한글 변환 매핑
eng_to_kor = {
    "Backend": "백엔드",
    "Frontend": "프론트엔드",
    "Fullstack": "풀스택",
    "Engineer": "엔지니어",
    "Developer": "개발자",
    "AI": "인공지능",
    "ML": "머신러닝",
    "Data": "데이터",
    "Scientist": "사이언티스트",
    "Analyst": "분석가",
    "Cloud": "클라우드",
    "DevOps": "데브옵스",
    "Security": "보안",
    "Manager": "매니저",
    "Lead": "리드",
    "Architect": "아키텍트",
    "Software": "소프트웨어",
    "Android": "안드로이드",
    "Python": "파이썬",
}

def translate_eng_to_kor_with_original(text):
    """영어를 한글로 변환하면서 원래 영어도 함께 저장"""
    pattern = re.compile(r"\b(" + "|".join(eng_to_kor.keys()) + r")\b")
    return pattern.sub(lambda x: f"{eng_to_kor[x.group()]} ({x.group()})", text)

def preprocess_job_details(details):
    """특정 컬럼 전처리: 단어 삭제 및 채용절차 값 처리"""
    remove_words_map = {
        "근무지역_상세": ["지도보기·주소복사"],
    }
    
    for key, words in remove_words_map.items():
        if key in details and details[key] != "정보 없음":
            for word in words:
                details[key] = details[key].replace(word, "").strip()

    # 모든 컬럼에서 빈 값, 공백 문자열, 길이가 1 이하면 "정보 없음" 처리
    for key in details:
        if not details[key].strip() or len(details[key]) <= 1:
            details[key] = "정보 없음"

    return details

# skill 데이터 전처리 함수 추가
def preprocess_skill(skill_text):
    """skill 데이터를 · 기호는 ','로 변경하고, 엔터는 공백으로 변환"""
    return skill_text.replace("·", ",").replace("\n", "").strip()

def scrape_job_details(job_link):
    """공고 상세 정보 크롤링"""
    try:
        response = requests.get(job_link)
        soup = BeautifulSoup(response.text, 'html.parser')

        details = {}
        detail_selectors = {
            '주요업무': 'body > main > div > div > section > div.position_info > dl:nth-child(3) > dd > pre',
            '자격요건': 'body > main > div > div > section > div.position_info > dl:nth-child(4) > dd > pre',
            '우대사항': 'body > main > div > div > section > div.position_info > dl:nth-child(5) > dd > pre',
            '복지_및_혜택': 'body > main > div > div > section > div.position_info > dl:nth-child(6) > dd > pre',
            '채용절차': 'body > main > div > div > section > div.position_info > dl:nth-child(7) > dd > pre',
            '학력': 'body > main > div > div.sc-10492dab-4.kvnCkd > section > div.sc-b12ae455-0.ehVsnD > dl:nth-child(3) > dd',
            '근무지역_상세': 'body > main > div > div > section > div.sc-b12ae455-0.ehVsnD > dl:nth-child(5) > dd > ul > li',
            '마감일자': 'body > main > div > div > section > div.sc-b12ae455-0.ehVsnD > dl:nth-child(4) > dd'
        }

        for key, selector in detail_selectors.items():
            try:
                element = soup.select_one(selector)
                text = element.get_text(strip=True) if element else "정보 없음"
                details[key] = text
            except:
                details[key] = "정보 없음"

        # 전처리 적용
        return preprocess_job_details(details)
    
    except Exception as e:
        print(f"상세 정보 크롤링 중 오류 발생: {e}")
        return {}


def scrape_jobs():
    """채용 공고 크롤링"""
    try:
        chromedriver_autoinstaller.install()

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)

        url = "https://jumpit.saramin.co.kr/positions?career=0&sort=rsp_rate"
        driver.get(url)
        time.sleep(5)

        last_height = driver.execute_script("return document.body.scrollHeight")  
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  
            time.sleep(2)  
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:  
                break
            last_height = new_height

        job_data = []
        job_elements = driver.find_elements(By.XPATH, "//section/div")
        print(f"총 {len(job_elements)}개의 공고를 찾았습니다.")
        

        for job_element in job_elements:
            try:
                title = WebDriverWait(job_element, 10).until(
                    EC.presence_of_element_located((By.XPATH, ".//a/div[3]/h2"))
                ).text.strip()
                company_name = job_element.find_element(By.XPATH, ".//a/div[3]/div/span").text.strip()
                skill = job_element.find_element(By.XPATH, ".//a/div[3]/ul[1]").text.strip()
                loc = job_element.find_element(By.XPATH, ".//a/div[3]/ul[2]/li[1]").text.strip()
                condition = job_element.find_element(By.XPATH, ".//a/div[3]/ul[2]/li[2]").text.strip()
                date = job_element.find_element(By.XPATH, ".//a/div[2]/div[1]/span").text.strip()
                job_url = job_element.find_element(By.TAG_NAME, "a").get_attribute("href")

                # 제목에 한글 변환 + 원래 영어 추가
                title = translate_eng_to_kor_with_original(title)
                skill = preprocess_skill(skill)
                job_data.append((title, company_name, skill, loc, condition, date, job_url))

            except Exception as e:
                print(f"Error: {e}")

        driver.quit()
        return job_data
    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
        return []

def save_to_db(job_data):
    """DB에 크롤링한 데이터 저장"""
    cursor = db.cursor()
    saved_job_count = 0
    
    for job in job_data:
        title, company_name, skill, loc, condition, date, job_url = job
        
        # 'D-day'인 데이터 제외
        if date.strip().lower() == 'd-day':
            print(f"'{title}' 공고는 'D-day'이므로 제외됨.")
            continue

        # 상세 정보 크롤링
        details = scrape_job_details(job_url)

        insert_query = """
        INSERT INTO job_posting_new (제목, 회사명, 사용기술, 근무지역, 근로조건, 모집기간, 링크, 주요업무, 자격요건, 우대사항, 복지_및_혜택, 채용절차, 학력, 근무지역_상세, 마감일자)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(insert_query, (title, company_name, skill, loc, condition, date, job_url, *details.values()))
            db.commit()
            saved_job_count += 1  # 저장된 공고 카운트 증가
        except Exception as e:
            print(f"DB 저장 중 오류 발생: {e}")
            db.rollback()
    
    cursor.close()
    print(f"총 {saved_job_count}개의 공고 DB 저장 완료!")

def main():
    print("채용 정보를 크롤링하는 중...")
    job_data = scrape_jobs()
    
    if job_data:
        save_to_db(job_data)
    else:
        print("저장할 데이터가 없습니다.")

if __name__ == "__main__":
    create_saved_jobs_table()
    main()
