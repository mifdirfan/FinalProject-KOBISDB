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

def search_movies_advanced(filters, page=1, per_page=100):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            joins = """
                FROM 영화 m
                LEFT JOIN 영화_감독 md ON m.Mid = md.Mid
                LEFT JOIN 감독 d ON md.Did = d.Did
                LEFT JOIN 영화_장르 mg ON m.Mid = mg.Mid
                LEFT JOIN 장르 g ON mg.Gid = g.Gid
                LEFT JOIN 영화_제작국가 mc ON m.Mid = mc.Mid
                LEFT JOIN 제작국가 c ON mc.Cid = c.Cid
                LEFT JOIN 영화_제작사 mco ON m.Mid = mco.Mid
                LEFT JOIN 제작사 co ON mco.Pid = co.Pid
            """
            
            conditions = []
            params = []

            if filters.get('title'):
                conditions.append("(m.영화명 LIKE %s OR m.영문명 LIKE %s)")
                params.extend(['%' + filters['title'] + '%', '%' + filters['title'] + '%'])
            if filters.get('director'):
                conditions.append("d.감독명 LIKE %s")
                params.append('%' + filters['director'] + '%')

            if filters.get('year_from'):
                conditions.append("m.제작연도 >= %s")
                params.append(filters['year_from'])
            if filters.get('year_to'):
                conditions.append("m.제작연도 <= %s")
                params.append(filters['year_to'])

            if filters.get('genres'):
                placeholders = ', '.join(['%s'] * len(filters['genres']))
                conditions.append(f"g.장르명 IN ({placeholders})")
                params.extend(filters['genres'])

            if filters.get('nations'):
                placeholders = ', '.join(['%s'] * len(filters['nations']))
                conditions.append(f"c.제작국가 IN ({placeholders})")
                params.extend(filters['nations'])

            name_idx = filters.get('name_index')
            if name_idx:
                hangul_ranges = {
                    'ㄱ': ('가', '나'), 'ㄴ': ('나', '다'), 'ㄷ': ('다', '라'),
                    'ㄹ': ('라', '마'), 'ㅁ': ('마', '바'), 'ㅂ': ('바', '사'),
                    'ㅅ': ('사', '아'), 'ㅇ': ('아', '자'), 'ㅈ': ('자', '차'),
                    'ㅊ': ('차', '카'), 'ㅋ': ('카', '타'), 'ㅌ': ('타', '파'),
                    'ㅍ': ('파', '하'), 'ㅎ': ('하', '힣')
                }
                if name_idx in hangul_ranges:
                    start, end = hangul_ranges[name_idx]
                    conditions.append("(m.영화명 >= %s AND m.영화명 < %s)")
                    params.extend([start, end])
                else:
                    conditions.append("(m.영화명 LIKE %s OR m.영문명 LIKE %s)")
                    params.extend([name_idx + '%', name_idx + '%'])

            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)

            count_sql = "SELECT COUNT(DISTINCT m.Mid) AS total " + joins + where_clause
            cursor.execute(count_sql, tuple(params))
            total_count = cursor.fetchone()['total']

            offset = (page - 1) * per_page
            sql = """
                SELECT 
                    m.Mid, m.영화명, m.영문명, m.제작연도, m.유형, m.제작상태,
                    GROUP_CONCAT(DISTINCT d.감독명 SEPARATOR ', ') AS 감독,
                    GROUP_CONCAT(DISTINCT g.장르명 SEPARATOR ', ') AS 장르,
                    GROUP_CONCAT(DISTINCT c.제작국가 SEPARATOR ', ') AS 국적,
                    GROUP_CONCAT(DISTINCT co.제작사명 SEPARATOR ', ') AS 제작사
                """ + joins + where_clause + f" GROUP BY m.Mid ORDER BY m.제작연도 DESC LIMIT {per_page} OFFSET {offset}"
            
            cursor.execute(sql, tuple(params))
            results = cursor.fetchall()
            
            return results, total_count
    finally:
        connection.close()

def get_filter_options():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT 제작연도 FROM 영화 WHERE 제작연도 IS NOT NULL ORDER BY 제작연도 DESC")
            years = cursor.fetchall()
            cursor.execute("SELECT DISTINCT 장르명 FROM 장르 ORDER BY 장르명 ASC")
            genres = cursor.fetchall()
            cursor.execute("SELECT DISTINCT 제작국가 FROM 제작국가 ORDER BY 제작국가 ASC")
            nations = cursor.fetchall()
            return years, genres, nations
    finally:
        connection.close()

def get_movie_details(mid):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT 
                    m.Mid, m.영화명, m.영문명, m.제작연도, m.유형, m.제작상태,
                    GROUP_CONCAT(DISTINCT d.감독명 SEPARATOR ', ') AS 감독,
                    GROUP_CONCAT(DISTINCT g.장르명 SEPARATOR ', ') AS 장르,
                    GROUP_CONCAT(DISTINCT c.제작국가 SEPARATOR ', ') AS 국적,
                    GROUP_CONCAT(DISTINCT co.제작사명 SEPARATOR ', ') AS 제작사
                FROM 영화 m
                LEFT JOIN 영화_감독 md ON m.Mid = md.Mid
                LEFT JOIN 감독 d ON md.Did = d.Did
                LEFT JOIN 영화_장르 mg ON m.Mid = mg.Mid
                LEFT JOIN 장르 g ON mg.Gid = g.Gid
                LEFT JOIN 영화_제작국가 mc ON m.Mid = mc.Mid
                LEFT JOIN 제작국가 c ON mc.Cid = c.Cid
                LEFT JOIN 영화_제작사 mco ON m.Mid = mco.Mid
                LEFT JOIN 제작사 co ON mco.Pid = co.Pid
                WHERE m.Mid = %s
                GROUP BY m.Mid
            """
            cursor.execute(sql, (mid,))
            return cursor.fetchone()
    finally:
        connection.close()