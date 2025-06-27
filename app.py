import streamlit as st
import pandas as pd
import pickle
import requests
import gdown
import os
from datetime import datetime

# --- Session State Initialization ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "email_verified" not in st.session_state:
    st.session_state["email_verified"] = False

# --- Simulated Aadhaar DOB Retrieval ---
def dob(aadhaar_number):
    fake_dob = "2005-04-01"  # Replace this with real API logic if needed
    return datetime.strptime(fake_dob, "%Y-%m-%d")

# --- Download Files from Google Drive ---
@st.cache_data
def load_files():
    files = {
        "movie_dict.pkl": "1LGG7tJwJI6Uhtikb-muxnPdXBEDyI4E3",
        "similarity.pkl": "1iczjeOnLTRx3-jJRlF1_vykYzSvH2zzL",
        "extra1.pkl": "1xnpa51GaP0ONM2LXFe0CW2v_VWXE5HsA",
        "extra2.pkl": "1Bhv_SGDq4Bo1YSRCw8-A8sShYht4Qq_s"
    }
    for filename, file_id in files.items():
        if not os.path.exists(filename):
            url = f"https://drive.google.com/uc?id={file_id}"
            gdown.download(url, filename, quiet=False)

    movie_dict = pickle.load(open("movie_dict.pkl", "rb"))
    similarity = pickle.load(open("similarity.pkl", "rb"))
    return pd.DataFrame(movie_dict), similarity

# --- Fetch Poster & Rating ---
def fetch_movie_data(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        poster_url = f"https://image.tmdb.org/t/p/w500/{data['poster_path']}" if data.get('poster_path') else "https://via.placeholder.com/200"
        rating = round(data.get('vote_average', 0), 1)
        return poster_url, rating
    except:
        return "https://via.placeholder.com/200", 0

# --- Recommend Function ---
def recommend(movie):
    if movie not in movies['title'].values:
        st.error("Movie not found! Please select a valid movie.")
        return [], [], [], []

    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_indices = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:7]

    recommended_movies, posters, links, ratings = [], [], [], []

    for i in movie_indices:
        movie_id = movies.iloc[i[0]].movie_id
        title = movies.iloc[i[0]].title
        poster, rating = fetch_movie_data(movie_id)

        recommended_movies.append(title)
        posters.append(poster)
        links.append(f"https://www.themoviedb.org/movie/{movie_id}")
        ratings.append(rating)

    return recommended_movies, posters, links, ratings

# --- UI Header ---
def display_header():
    st.image("https://wes.eletsonline.com/assets/images/haridwar-logo-500.png", width=200)
    st.markdown('<h1 style="color:blue;">Haridwar University</h1>', unsafe_allow_html=True)
    st.markdown('<h2 style="color:green;">Movie Recommendation System 🎬</h2>', unsafe_allow_html=True)

# --- App Logic ---
if not st.session_state["authenticated"]:
    display_header()
    st.markdown('<h2 style="color:red;">Age Verification</h2>', unsafe_allow_html=True)

    aadhaar_number = st.text_input("Enter your Aadhaar Card Number:", max_chars=12)
    if st.button("Verify Age"):
        if len(aadhaar_number) == 12 and aadhaar_number.isdigit():
            try:
                dob_value = dob(aadhaar_number)
                age = (datetime.today() - dob_value).days // 365
                if age >= 18:
                    st.success("Age Verified ✅")
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error(f"Access Denied! You are only {age} years old. Must be 18+.")
            except:
                st.error("Error verifying age. Please try again.")
        else:
            st.warning("Enter a valid 12-digit Aadhaar number.")

elif not st.session_state["email_verified"]:
    st.subheader("🔐 Email & Password Setup")
    email = st.text_input("Enter your Email")
    password = st.text_input("Password", type="password")
    if st.button("Submit"):
        if email and password:
            with open("users.txt", "a") as file:
                file.write(f"{email},{password}\n")
            st.success("Account Created & Saved Successfully!")
            st.session_state["email_verified"] = True
            st.rerun()
        else:
            st.warning("Please enter both email and password.")

else:
    display_header()
    movies, similarity = load_files()

    if not movies.empty:
        selected_movie = st.selectbox("Choose a movie:", movies['title'].values)
        if st.button("Recommend"):
            names, posters, links, ratings = recommend(selected_movie)
            if names:
                cols = st.columns(len(names))
                for i, col in enumerate(cols):
                    with col:
                        st.image(posters[i], width=180)
                        st.markdown(f"**{names[i]}**")
                        st.markdown(f"⭐ Rating: {ratings[i]}")
                        st.markdown(f"[More Info]({links[i]})", unsafe_allow_html=True)
            else:
                st.warning("No recommendations found.")

    if st.button("Logout"):
        st.session_state["authenticated"] = False
        st.session_state["email_verified"] = False
        st.rerun()
