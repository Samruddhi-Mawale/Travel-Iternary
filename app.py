import streamlit as st
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import date, timedelta

# Load API keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(page_title="🎒 AI Travel Planner", layout="wide")
st.title("🎒 AI Travel Planner for Students")
st.write("Plan your perfect, budget-friendly trip with help from AI!")

# User Input Form
with st.form("trip_form"):
    destination = st.text_input("Destination City", "Goa")
    days = st.number_input("Number of Days", min_value=1, max_value=15, value=3)
    budget = st.text_input("Budget (₹ or $)", "₹5000")
    interests = st.text_input("Interests (comma separated)", "beaches, food, culture")
    start_date = st.date_input("Trip Start Date", value=date.today())
    transportation = st.selectbox("Transportation Mode", ["Airline", "Train", "Road"])
    submitted = st.form_submit_button("✨ Generate Itinerary")

# Google Maps Places API with fallback
def get_top_places(destination):
    fallback_places = [
        "Local Museum",
        "City Park",
        "Famous Temple",
        "Popular Market",
        "Main Beach"
    ]
    try:
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=tourist+attractions+in+{destination}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if "results" in data and len(data["results"]) > 0:
            places = []
            for place in data["results"][:5]:
                name = place["name"]
                address = place.get("formatted_address", "Address not available")
                rating = place.get("rating", "No rating")
                places.append(f"{name} (⭐ {rating}) - {address}")
            return places
        else:
            st.warning(f"No results from Google API. Using default attractions for {destination}.")
            return fallback_places
    except Exception as e:
        st.error(f"Error fetching places: {e}. Using default attractions.")
        return fallback_places

# OpenAI itinerary generator
def generate_itinerary(destination, days, interests, budget, places, start_date, transportation):
    places_list = "\n".join(places)
    prompt = f"""
    You are an AI travel planner for students with a limited budget.

    Destination: {destination}
    Days: {days}
    Interests: {interests}
    Budget: {budget}
    Start Date: {start_date}
    Transportation: {transportation}

    Must include these popular places:
    {places_list}

    Create a detailed, day-by-day itinerary with:
    - Morning, afternoon, evening activities
    - Approximate daily cost
    - Budget-saving tips
    - Student-friendly suggestions
    - Include the date for each day based on the start date
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700,
        temperature=0.8
    )
    return response.choices[0].message.content

# Main logic
if submitted:
    with st.spinner("🧭 Finding places and creating your trip plan..."):
        try:
            places = get_top_places(destination)
            itinerary = generate_itinerary(destination, days, interests, budget, places, start_date, transportation)
            
            st.subheader("📍 Top Attractions")
            for p in places:
                st.write("- " + p)
            
            st.subheader("🗓️ Your AI-Generated Itinerary")
            st.write(itinerary)
        except Exception as e:
            st.error(f"Error: {e}")
