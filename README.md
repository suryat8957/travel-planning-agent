<div align="center">

# ✈️ ATLAS
### *Autonomous Multi-Agent Travel Desk & Itinerary Architect*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent%20StateGraph-FF6F00?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Google Gemini](https://img.shields.io/badge/LLM-Gemini%203.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://aistudio.google.com/)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit%20Airmail-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tavily Search](https://img.shields.io/badge/Web%20Grounding-Tavily%20AI-00C49F?style=for-the-badge)](https://tavily.com/)
[![Aviationstack](https://img.shields.io/badge/Aviation-Aviationstack%20API-7952B3?style=for-the-badge)](https://aviationstack.com/)

<p align="center">
  <b>Transform natural language travel queries into flight-verified, stay-scouted, day-by-day bespoke itineraries—complete with vintage airmail boarding passes, persistent session vaults, and an interactive AI concierge.</b>
</p>

[Key Features](#-key-features) •
[System Architecture](#-system-architecture) •
[The Agent Fleet](#-the-4-agent-autonomous-fleet) •
[The Airmail UI](#-the-airmail-ui-experience) •
[Quickstart](#-quickstart-guide) •
[Configuration](#-configuration--api-keys) •
[State Graph](#-state-schema--data-flow) •
[Roadmap](#-future-roadmap)

---

</div>

## 🌟 Overview: Why Atlas?

Planning an unforgettable trip normally means juggling **dozens of open tabs**: flight aggregators, booking portals, travel blogs, currency converters, mapping tools, and messy scratchpads.

**Atlas changes that.** Built on **LangGraph** and powered by **Google Gemini 3.5 Flash**, Atlas deploys a specialized fleet of autonomous agents that execute sequentially over a shared, stateful graph:
1. **Validates & queries live airline routes** via Aviationstack.
2. **Scouts curated accommodations and neighborhood stays** via Tavily AI Web Search.
3. **Architects detailed day-by-day itineraries** matching travel styles, party size, and budgets.
4. **Synthesizes an executive travel brief**, issuing a procedural vintage boarding pass and unlocking an interactive AI travel concierge.

Every trip is checkpointed into an embedded **SQLite Trip Vault**, allowing seamless restoration, auditing, and instant offline retrieval.

---

## ⚡ Key Features

- **🤖 LangGraph StateGraph Architecture**: Built on deterministic, stateful multi-agent execution with robust error isolation and checkpointing.
- **🛫 Live Aviation Verification**: Extracts departure and arrival cities, maps IATA airport codes, filters cancelled/past flights, and standardizes local airport departure/arrival times.
- **🏨 Live Web-Grounding for Stays**: Searches real-time web intelligence for boutique hotels, neighborhood gems, and verified traveler recommendations.
- **📅 Smart Day-by-Day Itineraries**: Generates structured, narrative morning-to-night travel schedules with paced activities, culinary hotspots, and cultural highlights.
- **🎟️ Vintage Airmail UI ("Atlas Desk")**:
  - Procedural Boarding Pass with dynamic flight seat assignment, boarding gate generation, and authentic postal postmark stamp.
  - Animated flight radar pipeline tracker illustrating agent execution in real time.
  - Tabbed dossiers for high-level briefs, day plans, flights, accommodations, and raw telemetry.
- **💬 Conversational AI Concierge**: Embedded chat companion with conversation memory to adapt your itinerary (e.g., *"Make it budget friendly"*, *"Add a rainy-day museum backup"*, or *"Generate a complete packing list"*).
- **🗄️ SQLite Trip Vault**: Instant session recovery. Switch between past trip threads at any time without losing context.
- **📥 One-Click Export**: Export comprehensive trip dossiers as clean GitHub-flavored Markdown (`trip-brief.md`) or structured JSON payloads (`trip-data.json`).
- **🔍 Full Observability**: Built-in support for LangSmith tracing to monitor token usage, node latency, and tool calls.

---

## 🏛️ System Architecture

Atlas coordinates a linear multi-agent workflow where each node specializes in one phase of trip curation before handing over the updated state to the next specialist.

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#1F5FBF', 'primaryTextColor': '#ffffff', 'primaryBorderColor': '#14213D', 'lineColor': '#D7263D', 'secondaryColor': '#E9EEF2', 'tertiaryColor': '#FFFFFF'}}}%%
flowchart TD
    subgraph Client ["🖥️ Streamlit Airmail Desk UI"]
        UI_Input["📝 Travel Prompt & Meta Controls<br/><i>(Days, Travelers, Budget, Vibes)</i>"]
        UI_Ticket["🎟️ Vintage Boarding Pass Generator"]
        UI_Tabs["📑 Tabbed Dossier & Day Breakdown"]
        UI_Concierge["💬 Live AI Concierge Assistant"]
    end

    subgraph LangGraph ["⚡ LangGraph StateGraph Pipeline"]
        StartNode([START]) --> FlightAgent["✈️ flight_agent<br/><i>Route Extraction & Aviation Query</i>"]
        FlightAgent --> HotelAgent["🏨 hotel_agent<br/><i>Live Web Scouting</i>"]
        HotelAgent --> ItineraryAgent["📅 itinerary_agent<br/><i>Day-by-Day Scheduling</i>"]
        ItineraryAgent --> FinalAgent["📝 final_agent<br/><i>Dossier Synthesis</i>"]
        FinalAgent --> EndNode([END])
    end

    subgraph Tools ["🛠️ External Services & Tools"]
        Aviationstack["📡 Aviationstack REST API<br/><i>Live Airport Schedules & IATA</i>"]
        Tavily["🔎 Tavily AI Search API<br/><i>Real-time Accommodation Web Data</i>"]
        Gemini["🧠 Google Gemini 3.5 Flash<br/><i>Fast Reasoning & Structuring</i>"]
    end

    subgraph Memory ["💾 Checkpoint Persistence"]
        SQLiteCheckpointer[("🗄️ SQLiteSaver<br/><i>travel_agent.db</i>")]
    end

    %% Wiring
    UI_Input -->|Stream updates| StartNode
    FlightAgent <-->|IATA Extraction| Gemini
    FlightAgent <-->|Flight Status & Schedules| Aviationstack
    HotelAgent <-->|Targeted Stays Search| Tavily
    ItineraryAgent <-->|Structured Day Planning| Gemini
    FinalAgent <-->|Executive Trip Brief| Gemini
    
    LangGraph <-->|State Snapshot per Thread| SQLiteCheckpointer
    EndNode --> UI_Ticket
    EndNode --> UI_Tabs
    UI_Tabs --> UI_Concierge
```

---

## 🤖 The 4-Agent Autonomous Fleet

| Agent | Module | Primary Capability | Key Outputs |
| :--- | :--- | :--- | :--- |
| **1. Flight Agent** | `tools/flight_tool.py` | Uses Gemini to infer departure/arrival cities and validate 3-letter IATA codes. Queries Aviationstack API, purges cancelled/past flights, formats local airport times. | `flight_results` string with airline names, flight numbers, terminals, local departure/arrival timestamps, and disclaimer. |
| **2. Hotel Agent** | `tools/tavily_tool.py` | Constructs targeted search queries based on traveler requirements. Executes Tavily Search API with deduplication and domain scoring. | `hotel_results` with verified links, descriptions, and curated neighborhood recommendations. |
| **3. Itinerary Agent** | `backend.py` | Ingests the flight schedules, lodging data, and trip duration to formulate a paced, culturally immersive day-by-day schedule. | `itinerary` markdown containing segmented days (Morning, Afternoon, Evening, Dining). |
| **4. Final Agent** | `backend.py` | Synthesizes an executive overview summarizing logistics, neighborhood tips, key highlights, and departure notices into a cohesive brief. | `final` trip brief presented on the main ticket dashboard. |

---

## 🎨 The Airmail UI Experience

Atlas features a bespoke Streamlit frontend inspired by vintage transcontinental airmail stationery:

<div align="center">

```
+---------------------------------------------------------------------------------------+
|  ATLAS AIRMAIL TRAVEL DESK                                   PASSENGER: Surya         |
+---------------------------------------------------------------------------------------+
|  [FLIGHTS: Done in 2.1s] -> [STAYS: Done in 1.4s] -> [ITINERARY: Done] -> [FINAL]     |
|                                                                                       |
|  +==========================================================+----------------------+  |
|  |  AIRMAIL BOARDING PASS                                   |  SEAT: 14A           |  |
|  |  PREPARED FOR: Surya                                     |  GATE: C12           |  |
|  |  DESTINATION: 5 days in Kyoto from Delhi (Culture, Food) |  DATE: 21 OCT 2026   |  |
|  |  Travelers: 2  |  Length: 5 Days  |  Budget: Comfortable |  (Postmark Stamp)    |  |
|  +==========================================================+----------------------+  |
|                                                                                       |
|  [ Trip Brief ]   [ Day by Day ]   [ Flights ]   [ Stays ]   [ Run Details ]          |
|  ---------------------------------------------------------------------------          |
|  Day 1: Arrival & Gion Lanterns       |  Day 2: Arashiyama Bamboo & Tea               |
|  Day 3: Fushimi Inari at Dawn         |  Day 4: Nishiki Market Food Crawl             |
|                                                                                       |
|  💬 ASK CONCIERGE: [Make it cheaper] [Rainy day plan] [Packing list] [Food stops]    |
+---------------------------------------------------------------------------------------+
```

</div>

- **Custom Typography**: Embedded Google Fonts (`Bricolage Grotesque` for headers and `Newsreader` for editorial reading).
- **Procedural Boarding Pass**: Every trip generates a deterministically hashed seat, boarding gate, and vector postmark seal.
- **Flight Radar Animation**: Real-time pulsing radar indicator tracking the active agent node through the graph.
- **Interactive Trip Vault**: Sidebar history permitting instant time-travel between different planned trips saved in SQLite.
- **Concierge Quick-Action Chips**: One-click prompt enhancements to immediately refine results.

---

## 📂 Project Structure

```bash
travel-planning-agent/
├── .env.example              # Environment variables template
├── .gitignore                # Production gitignore rules
├── LICENSE                   # MIT License
├── README.md                 # Project documentation & architecture
├── requirements.txt          # Python dependencies
├── backend.py                # LangGraph StateGraph, agents, and SQLiteSaver
├── app.py                    # Streamlit "Atlas" Airmail UI & Concierge engine
├── travel_agent.db           # SQLite database storing checkpoint threads
└── tools/
    ├── __init__.py
    ├── flight_tool.py        # Aviationstack API client + Gemini IATA extractor
    └── tavily_tool.py        # Tavily AI Search client for hotels & stays
```

---

## 🚀 Quickstart Guide

### 1. Clone the Repository

```bash
git clone https://github.com/suryat8957/travel-planning-agent.git
cd travel-planning-agent
```

### 2. Set Up a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the provided template and insert your API keys:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Open `.env` in your editor and provide the keys described in the [Configuration](#-configuration--api-keys) section below.

### 5. Launch the Application

#### Option A: Interactive Streamlit Airmail Desk (Recommended)
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`.

#### Option B: Terminal CLI Mode
```bash
python backend.py
```

---

## 🔑 Configuration & API Keys

Atlas relies on three primary APIs. Create accounts and grab free-tier API keys:

| Service | Environment Variable | Purpose | How to Obtain |
| :--- | :--- | :--- | :--- |
| **Google AI Studio** | `GEMINI_API_KEY` | Powers agent reasoning, IATA extraction, and itinerary creation. | [Get API Key](https://aistudio.google.com/app/apikey) |
| **Aviationstack** | `AVIATIONSTACK_API_KEY` | Real-time flight tracking, airline schedules, and airport status. | [Get API Key](https://aviationstack.com/) |
| **Tavily AI** | `TAVILY_API_KEY` | Search engine optimized for autonomous AI agents to scout stays. | [Get API Key](https://tavily.com/) |
| **LangSmith** *(Optional)* | `LANGCHAIN_API_KEY` | Real-time telemetry, token monitoring, and agent tracing. | [Get API Key](https://smith.langchain.com/) |

Your `.env` file should look like this:

```ini
GEMINI_API_KEY="AIzaSy..."
AVIATIONSTACK_API_KEY="15c0e5..."
TAVILY_API_KEY="tvly-dev-..."

# Optional Observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY="lsv2_pt_..."
LANGCHAIN_PROJECT=travel-planning-agent
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

---

## 📊 State Schema & Data Flow

Atlas manages a unified `TravelState` TypedDict defined in [`backend.py`](backend.py):

```python
class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]  # Accumulative message history
    user_query: str                                     # Raw or enriched traveler query
    flight_results: str                                 # Parsed flight data from Aviationstack
    hotel_results: str                                  # Curated stays from Tavily search
    itinerary: str                                      # Formatted day-by-day plan
    llm_calls: int                                      # Total LLM reasoning invocations
```

### State Transformation Cycle:
1. **User input** initializes `user_query` and appends a `HumanMessage`.
2. **`flight_agent`** extracts origin/destination, calls Aviationstack, writes to `flight_results`, and increments `llm_calls`.
3. **`hotel_agent`** takes the destination query, searches Tavily, writes markdown snippets to `hotel_results`, and increments `llm_calls`.
4. **`itinerary_agent`** synthesizes `user_query` + `flight_results` + `hotel_results` using Gemini 3.5 Flash to generate `itinerary`.
5. **`final_agent`** writes the conclusive summary brief and appends the final `AIMessage`.
6. State is committed to `travel_agent.db` via `SqliteSaver`.

---

## 💡 Example Queries to Try

Test the agent with diverse travel styles and constraints:

- ⛩️ **Cultural Expedition:**
  > *"5 days in Kyoto from Delhi in April. Temples, traditional tea houses, and street food markets."*
- 🏖️ **Budget Weekend:**
  > *"Long weekend in Goa from Delhi, beach shacks, live music, and sunsets under 25,000 INR."*
- 🎒 **Multi-City Adventure:**
  > *"10 days in Vietnam from Mumbai, Hanoi to Ho Chi Minh City, overnight Halong Bay cruise, and street food."*
- 🌅 **Luxury Honeymoon:**
  > *"6 nights in Santorini flying from Bangalore, quiet caldera views, private wine tastings, and sunset sailing."*

---

## 🛠️ Extensibility & Customization

### 1. Swapping the LLM Provider
Atlas uses `ChatGoogleGenerativeAI` by default, but thanks to LangChain's modular design, switching to OpenAI, Groq, or Anthropic takes just a two-line edit in [`backend.py`](backend.py):

```python
# To switch to Groq (ultra-low latency):
from langchain_groq import ChatGroq
llm = ChatGroq(model_name="llama-3.3-70b-versatile")

# To switch to OpenAI:
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o", temperature=0)
```

### 2. Switching Checkpoint Database (PostgreSQL)
For multi-user cloud deployments, replace `SqliteSaver` with `PostgresSaver`:
```python
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

pool = ConnectionPool(conninfo="postgresql://user:pass@localhost:5432/travel_db")
checkpointer = PostgresSaver(pool)
checkpointer.setup()
```

---

## ❓ Frequently Asked Questions & Troubleshooting

<details>
<summary><b>Q: I get "ValueError: Missing AVIATIONSTACK_API_KEY in your .env file"</b></summary>

Ensure your `.env` file exists in the root directory where you are running the script and contains valid values. Do not rename `.env.example` directly if you want to keep the template—make a copy named `.env`.
</details>

<details>
<summary><b>Q: Aviationstack returns "No flight records found"</b></summary>

Aviationstack's free-tier plan supports real-time flight records for major commercial routes within specific search windows. If a specific regional airport code has no scheduled flights in the free database, Atlas will gracefully report this and proceed with the lodging and itinerary phases.
</details>

<details>
<summary><b>Q: How do I clear the cached trips in the Trip Vault?</b></summary>

The Trip Vault stores records in `travel_agent.db`. To reset all past history, simply delete `travel_agent.db`. A clean database will be automatically recreated on your next run.
</details>

---

## 🗺️ Future Roadmap

- [ ] **PDF Itinerary Export**: Export full vintage boarding passes and itineraries as publication-ready PDFs.
- [ ] **Calendar Synchronization**: Export day-by-day plans as `.ics` files for Google Calendar, Apple Calendar, and Outlook.
- [ ] **Multi-Leg Flight Routing**: Support for multi-city hops and layover optimizations.
- [ ] **Live Currency & Budget Tracker**: Real-time currency conversions and localized budget breakdowns.
- [ ] **Weather Integration**: Weather forecasts via OpenWeatherMap API integrated into each day's wardrobe recommendations.

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

## 👨‍💻 Author & Acknowledgements

Created with passion by **Surya** ([@suryat8957](https://github.com/suryat8957)) • [suryat8957@gmail.com](mailto:suryat8957@gmail.com)

- **[LangChain & LangGraph](https://github.com/langchain-ai/langgraph)** for stateful agent orchestration.
- **[Google Gemini](https://ai.google.dev/)** for high-performance generative reasoning.
- **[Aviationstack](https://aviationstack.com/)** & **[Tavily](https://tavily.com/)** for real-time search APIs.
- **[Streamlit](https://streamlit.io/)** for the rapid interactive web frontend.

<div align="center">
  <sub>⭐ If you find Atlas useful, don't forget to star the repository! ⭐</sub>
</div>
