from flask import Flask, render_template, request
import database # Import your separate database file!

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    movie_results = []
    
    # If the user clicks the "Search" button on the webpage
    if request.method == 'POST':
        # Grab what they typed in the search bar
        search_query = request.form.get('movie_title_input')
        
        # Call your clean database function
        if search_query:
            movie_results = database.search_movies(search_query)

    # Render the HTML page and pass the results to it
    return render_template('index.html', movies=movie_results)

if __name__ == '__main__':
    app.run(debug=True)