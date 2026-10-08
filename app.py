import streamlit as st
import requests
import os
import math
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from datetime import date

# 1. Load Environment Variables
load_dotenv(find_dotenv())
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("⚠️ `GROQ_API_KEY` is missing in your `.env` file! Please add it.")
    st.stop()

# Initialize OpenAI client with Groq
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# 2. UI Setup
st.set_page_config(page_title="🎒 Global AI Travel Planner", layout="wide")
st.title("🎒 Global AI Travel Planner for Students")
st.write("Plan your budget trip anywhere in the world with real GPS coordinates and transit distances!")

with st.form("trip_form"):
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        destination = st.text_input("Destination City / Country", "Paris, France")
        days = st.number_input("Number of Days", min_value=1, max_value=15, value=3)
        budget = st.text_input("Budget (e.g. ₹8000, $500, €450)", "€500")
    with col_input2:
        interests = st.text_input("Interests", "art, architecture, food, local culture")
        start_date = st.date_input("Trip Start Date", value=date.today())
        transportation = st.selectbox("Transportation Mode", ["Walking/Metro", "Public Transit / Bus", "Train", "Rental / Cab"])
    
    submitted = st.form_submit_button("✨ Generate Itinerary & Distance Matrix")

# 3. Haversine Formula to Calculate Exact Distance Between Coordinates (in km)
def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

# 4. Worldwide Landmark & GPS Geocoder (OpenStreetMap)
def get_global_attractions(destination):
    headers = {'User-Agent': 'GlobalTravelPlannerApp/3.0 (academic_student_project)'}
    
    # 4a. Geocode City Center anywhere in the world
    city_url = f"https://nominatim.openstreetmap.org/search?q={destination}&format=json&limit=1"
    city_lat, city_lon = None, None
    try:
        res = requests.get(city_url, headers=headers, timeout=6)
        if res.status_code == 200 and len(res.json()) > 0:
            city_item = res.json()[0]
            city_lat = float(city_item["lat"])
            city_lon = float(city_item["lon"])
    except Exception:
        pass

    if city_lat is None:
        st.warning(f"Could not locate '{destination}'. Please check spelling or include the country name.")
        return []

    # 4b. Fetch real tourist attractions within that city
    queries = [
        f"top attractions in {destination}",
        f"tourism in {destination}",
        f"museums in {destination}",
        f"famous places in {destination}"
    ]

    places = []
    seen_names = set()

    for q in queries:
        try:
            search_url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=8"
            res = requests.get(search_url, headers=headers, timeout=6)
            if res.status_code == 200:
                for item in res.json():
                    raw_name = item.get("display_name", "")
                    clean_name = raw_name.split(",")[0].strip()
                    lat = float(item.get("lat", 0))
                    lon = float(item.get("lon", 0))

                    # Filter duplicates & verify distance is within reasonable city radius (50km)
                    if clean_name and clean_name not in seen_names:
                        dist_from_center = calculate_haversine_distance(city_lat, city_lon, lat, lon)
                        if dist_from_center <= 50.0:
                            seen_names.add(clean_name)
                            places.append({
                                "name": clean_name,
                                "lat": lat,
                                "lon": lon,
                                "dist_from_center_km": dist_from_center
                            })
                    if len(places) >= 6:
                        break
            if len(places) >= 6:
                break
        except Exception:
            continue

    # 4c. If no specific attractions were parsed, default to central districts of that city
    if not places:
        places.append({"name": f"{destination} City Center", "lat": city_lat, "lon": city_lon, "dist_from_center_km": 0.0})

    return places

# 5. Compute Distances between Consecutive Spots
def build_distance_table(places):
    distance_records = []
    for i in range(len(places) - 1):
        p1 = places[i]
        p2 = places[i + 1]
        dist = calculate_haversine_distance(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
        distance_records.append({
            "From": p1["name"],
            "To": p2["name"],
            "Distance (km)": f"{dist} km",
            "Est. Travel Time (Transit/Walk)": f"~{int(dist * 12)} mins" if dist < 5 else f"~{int(dist * 3)} mins (by vehicle)"
        })
    return pd.DataFrame(distance_records)

# 6. LLM Itinerary Generation Grounded on Exact Spots & Distances
def generate_itinerary(destination, days, interests, budget, places, start_date, transportation, distance_df):
    places_formatted = "\n".join([f"- {p['name']} (GPS: {p['lat']:.4f}, {p['lon']:.4f})" for p in places])
    
    distance_summary = ""
    if not distance_df.empty:
        distance_summary = "\n".join([f"- From {row['From']} to {row['To']}: {row['Distance (km)']} ({row['Est. Travel Time (Transit/Walk)']})" for _, row in distance_df.iterrows()])

    prompt = f"""
    You are an expert budget travel planner for students.

    Trip Overview:
    - Destination: {destination}
    - Duration: {days} Days
    - Interests: {interests}
    - Budget: {budget}
    - Start Date: {start_date}
    - Transportation: {transportation}

    Mandatory Verified Attractions to Visit:
    {places_formatted}

    Known Route Distances Between Consecutive Spots:
    {distance_summary}

    Requirements:
    1. Structure the itinerary day-by-day (Day 1, Day 2, etc.) matching the start date.
    2. ONLY use and visit the verified attractions listed above.
    3. Explicitly state the travel distance and estimated transit time between consecutive spots when moving between them.
    4. Provide budget-saving tips and estimated costs for student travelers.
    5. Organize activities into Morning, Afternoon, and Evening.
    """

    candidate_models = [
        "openai/gpt-oss-20b",
        "llama-3.3-70b-versatile",
        "qwen/qwen3.6-27b",
        "groq/compound-mini"
    ]
    
    for model_name in candidate_models:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6
            )
            return response.choices[0].message.content
        except Exception as err:
            if "model_not_found" in str(err) or "404" in str(err):
                continue
            raise err

    raise RuntimeError("No active models available on provider.")

# 7. Budget Split Visualization
def display_budget_chart(budget_str):
    categories = ["Accommodation", "Food & Dining", "Local Transport", "Attraction Tickets & Free Leisure"]
    proportions = [0.38, 0.28, 0.18, 0.16]
    
    df_budget = pd.DataFrame({"Category": categories, "Share": proportions})
    fig = px.pie(
        df_budget, 
        values="Share", 
        names="Category", 
        title=f"Estimated Budget Split ({budget_str})",
        hole=0.45,
        color_discrete_sequence=px.colors.sequential.Teal
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

# 8. Main Execution
if submitted:
    with st.spinner(f"🧭 Looking up verified spots in {destination} and computing route distances..."):
        try:
            places = get_global_attractions(destination)
            
            if not places:
                st.error("Could not find locations. Please try a valid city name like 'Paris, France', 'Tokyo, Japan', or 'Jaipur, India'.")
                st.stop()

            # Generate distance matrix
            dist_df = build_distance_table(places)

            # Generate itinerary using strictly these places
            itinerary = generate_itinerary(destination, days, interests, budget, places, start_date, transportation, dist_df)

            st.markdown("---")
            
            # Map & Places
            col_map, col_budget = st.columns([1.2, 0.8])
            
            with col_map:
                st.subheader(f"📍 Verified Map Spots in {destination}")
                df_map = pd.DataFrame(places)
                st.map(df_map[['lat', 'lon']], zoom=11)
            
            with col_budget:
                display_budget_chart(budget)

            # Display Point-to-Point Distances
            if not dist_df.empty:
                st.subheader("📏 Spot-to-Spot Distance & Transit Estimates")
                st.dataframe(dist_df, use_container_width=True)

            st.markdown("---")
            
            # Display Itinerary
            st.subheader("🗓️ Coordinated Day-by-Day Itinerary")
            st.markdown(itinerary)

            # Download
            st.download_button(
                label="📥 Download Detailed Itinerary (.txt)",
                data=f"TRAVEL ITINERARY: {destination.upper()}\n\n" + itinerary,
                file_name=f"{destination.replace(' ', '_')}_itinerary.txt",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"Error: {e}")