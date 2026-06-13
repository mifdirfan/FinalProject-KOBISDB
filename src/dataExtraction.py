import pandas as pd 
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
        charset='utf8mb4'
    )


def load_and_merge(file_path):
    print(f"Loading data from {file_path}")

    try:
        df_tab1 = pd.read_excel(file_path, sheet_name=0, skiprows=4)
        print("Tab 1 read successfully.")
        df_tab2 = pd.read_excel(file_path, sheet_name=1)
        print("Tab 2 read successfully.")
        
        movie_info_df = pd.concat([df_tab1, df_tab2], ignore_index=True)
        
        if '제작연도' in movie_info_df.columns:
            movie_info_df['제작연도'] = pd.to_numeric(movie_info_df['제작연도'], errors='coerce')
        
        movie_info_df = movie_info_df.astype(object).where(pd.notnull(movie_info_df), None)

        print("\nData loaded, merged, and cleaned successfully.")
        print(f"Total movies: {len(movie_info_df)}")
        return movie_info_df
    
    except FileNotFoundError:
        print(f"File not found at {file_path}")
    except Exception as e:
        print(f"An error occurred during loading: {e}")


def insert_data(movie_info_df):
    print("Starting data insertion...")

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        create_table_query = """
            CREATE TABLE IF NOT EXISTS movie_info(
            id int AUTO_INCREMENT primary key, 
            영화명 varchar(255), 
            영문명 varchar(255), 
            제작연도 int, 
            제작국가 varchar(100), 
            유형 varchar(50),
            장르 varchar(100), 
            제작상태 varchar(50), 
            감독 varchar(255), 
            제작사 varchar(255)
            )
        """
        cursor.execute(create_table_query)

        insert_query = """
            INSERT INTO movie_info(영화명, 영문명, 제작연도, 제작국가, 유형, 장르, 제작상태, 감독, 제작사)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for index, row in movie_info_df.iterrows():
            values = (
                row['영화명'], 
                row['영화명(영문)'], 
                row['제작연도'], 
                row['제작국가'], 
                row['유형'], 
                row['장르'],
                row['제작상태'], 
                row['감독'], 
                row['제작사']
            )
            cursor.execute(insert_query, values)

        connection.commit()
        print("All raw data successfully inserted in movie_info table.")

    except pymysql.MySQLError as e:
        print(f"MySQL Error during staging: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()


def normalized_table():
    print("Starting schema normalization...")

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        create_table_query = ["""
            CREATE TABLE IF NOT EXISTS 영화(
            Mid INT AUTO_INCREMENT PRIMARY KEY, 
            영화명 VARCHAR(255), 
            영문명 VARCHAR(255), 
            제작연도 INT, 
            유형 VARCHAR(50), 
            제작상태 VARCHAR(50)
            )
        """, 
        """
            CREATE TABLE IF NOT EXISTS 감독(
            Did INT AUTO_INCREMENT PRIMARY KEY, 
            감독명 VARCHAR(255)
            )
        """, 
        """
            CREATE TABLE IF NOT EXISTS 장르(
            Gid INT AUTO_INCREMENT PRIMARY KEY, 
            장르명 VARCHAR(100)
            )
        """,
        """
            CREATE TABLE IF NOT EXISTS 제작국가(
            Cid INT AUTO_INCREMENT PRIMARY KEY, 
            제작국가 VARCHAR(100)
            )
        """,
        """
            CREATE TABLE IF NOT EXISTS 제작사(
            Pid INT AUTO_INCREMENT PRIMARY KEY, 
            제작사명 VARCHAR(255)
            )
        """, 
        """
            CREATE TABLE IF NOT EXISTS 영화_감독(
            Mid INT, 
            Did INT, 
            PRIMARY KEY (Mid, Did), 
            FOREIGN KEY (Mid) REFERENCES 영화(Mid), 
            FOREIGN KEY (Did) REFERENCES 감독(Did)
            )
        """, 
        """
            CREATE TABLE IF NOT EXISTS 영화_장르(
            Mid INT, 
            Gid INT, 
            PRIMARY KEY (Mid, Gid), 
            FOREIGN KEY (Mid) REFERENCES 영화(Mid), 
            FOREIGN KEY (Gid) REFERENCES 장르(Gid)
            )
        """, 
        """
            CREATE TABLE IF NOT EXISTS 영화_제작국가(
            Mid INT, 
            Cid INT, 
            PRIMARY KEY (Mid, Cid), 
            FOREIGN KEY (Mid) REFERENCES 영화(Mid), 
            FOREIGN KEY (Cid) REFERENCES 제작국가(Cid)
            )
        """,
        """
            CREATE TABLE IF NOT EXISTS 영화_제작사(
            Mid INT, 
            Pid INT, 
            PRIMARY KEY (Mid, Pid), 
            FOREIGN KEY (Mid) REFERENCES 영화(Mid), 
            FOREIGN KEY (Pid) REFERENCES 제작사(Pid)
            )
        """]

        print("Creating normalized schema tables (with multi-attribute production companies)...")
        for query in create_table_query:
            cursor.execute(query)

        index_queries = [
            "CREATE INDEX idx_movie_name ON 영화(영화명)",
            "CREATE INDEX idx_movie_name_en ON 영화(영문명)", 
            "CREATE INDEX idx_director_name ON 감독(감독명)", 
            "CREATE INDEX idx_production_year ON 영화(제작연도)",
            "CREATE INDEX idx_company_name ON 제작사(제작사명)"
        ]

        for query in index_queries:
            try:
                cursor.execute(query)
            except pymysql.err.OperationalError as e:
                if e.args[0] == 1061:
                    pass 
                else:
                    print(f"Index Error: {e}")

        connection.commit()
        print("Normalization schema completed.")

    except pymysql.MySQLError as e:
        print(f"MySQL Schema Error: {e}")
    finally: 
        if 'connection' in locals() and connection.open:
            connection.close()


def transfer_data_to_normalized(movie_info_df):
    print("Starting data migration...")

    director_cache = {}
    genre_cache = {}
    country_cache = {}
    company_cache = {}

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        def process_multi_attribute(Mid, raw_string, entity_table, map_table, entity_col, map_col, cache):
            if not raw_string: 
                return 

            clean_str = str(raw_string).replace('[', '').replace(']', '').replace("'", "")
            items_list = clean_str.split(',')
            
            for item in items_list:
                clean_item = item.strip() 
                if not clean_item: 
                    continue
                
                if clean_item not in cache:
                    cursor.execute(f"INSERT INTO {entity_table} ({entity_col}) VALUES (%s)", (clean_item,))
                    cache[clean_item] = cursor.lastrowid
                
                entity_id = cache[clean_item]

                map_query = f"INSERT IGNORE INTO {map_table} (Mid, {map_col}) VALUES (%s, %s)"
                cursor.execute(map_query, (Mid, entity_id))

        print("Executing entity mapping sequences...")

        for index, row in movie_info_df.iterrows():
            Mid = index + 1 

            movie_query = """
                INSERT INTO 영화 (Mid, 영화명, 영문명, 제작연도, 유형, 제작상태)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            movie_value = (
                Mid, 
                row['영화명'], 
                row['영화명(영문)'], 
                row['제작연도'], 
                row['유형'], 
                row['제작상태']
            )
            cursor.execute(movie_query, movie_value)

            process_multi_attribute(Mid, row['감독'], '감독', '영화_감독', '감독명', 'Did', director_cache)
            process_multi_attribute(Mid, row['장르'], '장르', '영화_장르', '장르명', 'Gid', genre_cache)
            process_multi_attribute(Mid, row['제작국가'], '제작국가', '영화_제작국가', '제작국가', 'Cid', country_cache)
            process_multi_attribute(Mid, row['제작사'], '제작사', '영화_제작사', '제작사명', 'Pid', company_cache)

        connection.commit()
        print("Data migration to relational model successful.")

    except pymysql.MySQLError as e:
        print(f"MySQL Migration Error: {e}")
        connection.rollback()
    finally: 
        if 'connection' in locals() and connection.open:
            connection.close()


if __name__ == "__main__":
    EXCEL_FILE = 'FinalProject/data/영화정보 리스트_2026-06-08.xls'

    merged_data = load_and_merge(EXCEL_FILE)
    if merged_data is not None:
        insert_data(merged_data)
        normalized_table()
        transfer_data_to_normalized(merged_data)