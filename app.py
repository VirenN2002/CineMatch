from flask import Flask, request, render_template
import pickle
import requests
import pandas as pd

import os
import urllib.request

def download_if_not_exists(url, filename):
    if not os.path.exists(filename):
        print(f"Downloading {filename} from Google Drive...")
        urllib.request.urlretrieve(url, filename)

# Download files if not present
download_if_not_exists("https://drive.google.com/uc?id=1SVFyp11NvnAlFLKObC814UWxB3uedCIl", "similarity.pkl")
download_if_not_exists("https://drive.google.com/uc?id=1Y82WR67YZvXft0A0nBgX8ijw7O6t5-if", "movie_list.pkl")


app = Flask(__name__)


movies = pickle.load(open('movie_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))


TMDB_API_KEY = '1f45b7505a405d7ac828f422d5717eae'
TMDB_SEARCH_URL = 'https://api.themoviedb.org/3/search/movie'

def get_movie_poster(movie_name):
    params = {
        'api_key': TMDB_API_KEY,
        'query': movie_name
    }
    response = requests.get(TMDB_SEARCH_URL, params=params)
    data = response.json()
    if data['results']:
        return f"https://image.tmdb.org/t/p/w500{data['results'][0]['poster_path']}"
    return None

def recommend(movie):
    movie_lower = movie.lower()
    if movie_lower not in movies['title'].str.lower().values:
        return None
    index = movies[movies['title'].str.lower() == movie_lower].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movies = [movies.iloc[i[0]].title for i in distances[1:6]]
    return recommended_movies

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def get_movie_recommendations():
    movie_name = request.form['movie']
    recommendations = recommend(movie_name)
    
    if recommendations is None:
        return render_template('index.html', error="Movie not found. Please try again.")
    
    movie_images = []
    for movie in recommendations:
        try:
            response = requests.get(TMDB_SEARCH_URL, params={'api_key': TMDB_API_KEY, 'query': movie})
            response.raise_for_status()
            data = response.json()
            
            if 'results' in data and data['results']:
                movie_poster_path = data['results'][0]['poster_path'] if len(data['results']) > 0 else None
                movie_images.append(movie_poster_path)
            else:
                movie_images.append(None)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {movie}: {e}")
            movie_images.append(None)
    
    return render_template('recommend.html', movies=recommendations, images=movie_images, zip=zip)

if __name__ == '__main__':
    app.run(debug=True)
