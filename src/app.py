from flask import Flask, render_template, request, jsonify
import database # Import your separate database file!
import math

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    movie_results = []
    total_count = 0
    current_page = 1
    total_pages = 1
    
    years, genres, nations = database.get_filter_options()
    hangul_letters = ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    english_letters = [chr(i) for i in range(65, 91)]

    if request.method == 'POST':
        # Grab the requested page number, default to 1 if it doesn't exist
        current_page = int(request.form.get('current_page', 1))

        filters = {
            'title': request.form.get('movie_title_input', '').strip(),
            'director': request.form.get('director_input', '').strip(),
            'year_from': request.form.get('year_from', ''),
            'year_to': request.form.get('year_to', ''),
            'movie_types': request.form.getlist('movie_type'),
            'genres': request.form.getlist('genre_multi'),
            'nations': request.form.getlist('nation_multi'),
            'name_index': request.form.get('name_index', '')
        }
        
        # Unpack the two returned values
        movie_results, total_count = database.search_movies_advanced(filters, page=current_page, per_page=100)
        
        # Calculate total pages (e.g. 250 movies / 100 = 3 pages)
        total_pages = math.ceil(total_count / 100)

        max_visible_pages = 5
        
        # 1. Calculate the ideal start and end (current page right in the middle)
        start_page = max(1, current_page - 2)
        end_page = min(total_pages, start_page + max_visible_pages - 1)
        
        # 2. Fix the sliding window if we are near the very end
        if end_page - start_page + 1 < max_visible_pages:
            start_page = max(1, end_page - max_visible_pages + 1)


    return render_template('index.html', 
                           movies=movie_results, 
                           years=years, 
                           genres=genres, 
                           nations=nations,
                           hangul_letters=hangul_letters,
                           english_letters=english_letters,
                           current_page=current_page,
                           total_pages=total_pages,
                           total_count=total_count,
                           start_page=start_page, 
                           end_page=end_page)


@app.route('/movie/<int:mid>', methods=['GET'])
def movie_details(mid):
    details = database.get_movie_details(mid)
    if details:
        return jsonify(details)
    return jsonify({'error': 'Movie not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)