.astype(object).where(pd.notnull(movie_info_df), None)
        insert_query = """