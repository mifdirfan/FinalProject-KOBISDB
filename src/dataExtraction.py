import pandas as pd 
import pymysql

def load_and_merge(file_path):
    print(f"Loading data from {file_path}")

    try:
        df_tab1 = pd.read_excel(file_path, sheet_name=0, skiprows=4)
        print("Tab 1 read successfully.")
        df_tab2 = pd.read_excel(file_path, sheet_name=1)
        print("Tab 2 read successfully.")
        
        movie_info_df = pd.concat([df_tab1, df_tab2], ignore_index=True)
        

        print("\nData loaded and merged")
        print(f"Toatal movies : {len(movie_info_df)}")
        print(movie_info_df.head(10))


        return movie_info_df
    
    except FileNotFoundError:
        print(f"File not found at {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


def insert_data(movie_info_df):
    print("connecting to db...")

    try:
        connection = pymysql.connect(
            host='localhost', 
            user='root',
            password='dongyang',
            database='kobisdb',
            charset='utf8mb4'
        )

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
        print("table created")

        movie_info_df['제작연도'] = pd.to_numeric(movie_info_df['제작연도'], errors='coerce')
        movie_info_df = movie_info_df.astype(object).where(pd.notnull(movie_info_df), None)
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
        print("data inserted")

    except pymysql.MySQLError as e:
        print(f"MySQL Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("connection closed")



if __name__ == "__main__":
    EXCEL_FILE = 'FinalProject/data/영화정보 리스트_2026-06-08.xls'

    merged_data = load_and_merge(EXCEL_FILE)
    insert_data(merged_data)