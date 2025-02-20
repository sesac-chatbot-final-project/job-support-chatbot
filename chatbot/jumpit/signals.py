from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        charset="utf8mb4"
    )

@receiver(post_save, sender=User)
def add_user_to_customer_table(sender, instance, created, **kwargs):
    if created:
        try:
            db = get_db_connection()
            cursor = db.cursor()

            create_table_query = """
            CREATE TABLE IF NOT EXISTS customer (
                customer_id VARCHAR(20) PRIMARY KEY
            )
            """
            cursor.execute(create_table_query)
            db.commit()

            # 이미 존재하는지 확인 후, 없으면 추가
            cursor.execute("SELECT customer_id FROM customer WHERE customer_id = %s", (instance.username,))
            result = cursor.fetchone()
            if not result:
                insert_query = "INSERT INTO customer (customer_id) VALUES (%s)"
                cursor.execute(insert_query, (instance.username,))
                db.commit()
            cursor.close()
            db.close()
        except Exception as e:
            print(f"회원가입 후 customer 테이블 업데이트 중 오류 발생: {e}")