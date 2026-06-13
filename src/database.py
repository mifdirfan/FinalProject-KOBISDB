import pymysql
import os 
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),           
        user=os.getenv('DB_USER'),           
        password=os.getenv('DB_PASSWORD'),   
        database=os.getenv('DB_NAME'),       
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def search_movies(title_keyword):
    """Searches for movies by title and joins the director name."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Notice the JOINs to stitch your Phase 2 tables back together!
            sql = """
                SELECT m.영화명, m.제작연도, m.유형, d.감독이름 
                FROM 영화 m
                LEFT JOIN 영화_감독 md ON m.Mid = md.Mid
                LEFT JOIN 감독 d ON md.Did = d.Did
                WHERE m.영화명 LIKE %s
            """
            # Add wildcards for partial matching (e.g., search "Action" -> "%Action%")
            cursor.execute(sql, ('%' + title_keyword + '%',))
            return cursor.fetchall()
    finally:
        connection.close()