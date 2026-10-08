# 🎒AI-Driven Geospatial Travel Planner

An intelligent, full-stack travel planner designed for students and budget-conscious travelers. The application performs worldwide landmark geocoding via **OpenStreetMap (Nominatim)**, computes pairwise transit distances using the **Haversine formula**, and generates cost-optimized, date-aware itineraries using **Llama 3 hosted on Groq Cloud**.

---

## 🌟 Key Features

- **Worldwide Landmark Geocoding:** Fetches verified, global tourist attractions and precise GPS coordinates using OpenStreetMap (Nominatim API) with zero vendor lock-in or API keys.
- **Dynamic Route Logistics & Transit Estimation:** Uses the mathematical **Haversine formula** to calculate great-circle distances (in km) and transit times between consecutive spots.
- **LLM Grounding & Hallucination Prevention:** Injects real geospatial coordinates directly into prompt contexts, forcing the model to generate itineraries based strictly on verified locations.
- **Multi-Model Auto-Failover:** Built-in resilience mechanism that catches model deprecations (`404 model_not_found`) and switches dynamically across active Groq LLM candidates.
- **Interactive Visualizations:** Renders responsive GPS pin maps (`st.map`) and dynamic budget allocation donut charts (`plotly.express`).
- **Offline Itinerary Export:** Single-click download option generating clean `.txt` itineraries for offline travel use.

---

## 🏗️ Architecture & Technical Evolution

| Component | Initial Setup | Final Production Choice | Why the Shift? |
| :--- | :--- | :--- | :--- |
| **Geocoding & Places** | Google Maps Places API | **OpenStreetMap (Nominatim)** | Removed mandatory credit card requirements, billing overhead, and API restriction issues (`403 Forbidden`). Provides free, keyless global geocoding. |
| **LLM Inference** | OpenAI GPT Models | **Groq Cloud (Llama 3)** | Bypasses OpenAI's strict quota exhaustion errors (`429 Insufficient Quota`) while delivering high-throughput inference at zero cost via an OpenAI-compatible SDK client. |

---

## 🛠️ Tech Stack

- **Frontend & Dashboard:** [Streamlit](https://streamlit.io/)
- **AI Model & Inference:** Llama 3 via [Groq Cloud API](https://console.groq.com/) (using `openai` Python SDK)
- **Geospatial Data Engine:** [OpenStreetMap Nominatim API](https://nominatim.org/)
- **Data Manipulation & Analytics:** [Pandas](https://pandas.pydata.org/)
- **Data Visualization:** [Plotly Express](https://plotly.com/python/)
- **Routing Algorithms:** Great-Circle Haversine Formula

---

## 📁 Project Structure

```text
├── app.py                # Main Streamlit application with UI, geocoding, and LLM pipeline
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (excluded from Git via .gitignore)
├── .gitignore            # Git ignore file preventing API key leakage
└── README.md             # Project documentation
