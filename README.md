# AI Travel Agent

A multi-agent AI travel planning assistant built with LangGraph, Google Gemini, and Streamlit. Given a natural-language travel query, it autonomously searches real flights and hotels, generates a personalized day-by-day itinerary, and can email the result to you — with every step (which tool to call, when it's done) driven by the LLM's own decisions, not hardcoded logic.

## Features

- Natural language travel query input ("I want to travel to Paris from NYC from 2026-09-01 to 2026-09-08. Interests: museums, fine dining, nightlife.")
- Real-time flight search via the Skyscanner Flights API (RapidAPI)
- Real-time hotel search via the Booking.com API (RapidAPI), including destination-name resolution
- AI-generated daily itinerary tailored to the user's stated interests
- Human-in-the-loop email delivery: the agent pauses mid-run (via a LangGraph interrupt) to ask whether to email the itinerary, then resumes and sends it via SendGrid if approved
- Retry logic for transient LLM/API failures
- Automated test suite (`pytest`, fully mocked — no live API calls in CI)

## Architecture

```
User (Streamlit UI)
        |
        v
  LangGraph agent  <----------------------+
  (Gemini decides                          |
   which tool to call)                     |
        |                                  |
        v                                  |
  +----------------+----------------+      |
  |                |                |      |
flights_finder  hotels_finder  itinerary_planner
  |                |                |      |
  +----------------+----------------+------+
        (results loop back to the agent)
        |
        v  (once the LLM has no more tool calls)
  request_email_decision  --[interrupt: pause here]--> user decides
        |
        v  (resumed with Command(resume=...))
  SendGrid (if approved)  -->  END
```

The core loop lives in `agents/agent.py`: a LangGraph `StateGraph` alternates between asking the LLM what to do (`call_tools_llm`) and actually running whichever tool it requested (`invoke_tools`), until the LLM responds with no further tool calls. At that point the graph moves to `request_email_decision`, which calls LangGraph's `interrupt()` to genuinely pause execution — state is checkpointed via `MemorySaver`, keyed by a `thread_id` — and hands the itinerary back to the caller. The caller (`app.py`) resumes the same paused run later with `Command(resume=...)` once the user has made a decision.

## Tech stack

- **Language:** Python 3.13
- **Orchestration:** LangGraph (`StateGraph`, conditional edges, checkpointing, interrupts) + LangChain (message types, tool binding)
- **LLM:** Google Gemini (`gemini-flash-lite-latest`), via `langchain-google-genai` — free tier, no billing required
- **External data:** Skyscanner Flights and Booking.com, both via RapidAPI
- **Email:** SendGrid
- **UI:** Streamlit
- **Testing:** `pytest`, `unittest.mock`

## Setup

1. Clone the repo and `cd` into it.
2. Create an isolated environment: `conda create -n travel-agent python=3.13` then `conda activate travel-agent` (or use `python -m venv`).
3. `pip install -r requirements.txt`
4. Create a `.env` file in the project root (never committed — see `.gitignore`) with:
   ```
   GOOGLE_API_KEY=...
   RAPIDAPI_KEY=...
   SENDGRID_API_KEY=...
   ```
   - `GOOGLE_API_KEY`: free at aistudio.google.com.
   - `RAPIDAPI_KEY`: one key, but you must individually subscribe (free tier) to both "Skyscanner Flights" (by Crawlio) and "Booking COM" (by DataCrawler) on rapidapi.com.
   - `SENDGRID_API_KEY`: from sendgrid.com; also requires verifying a Single Sender identity before it can send mail.
5. Run it: `streamlit run app.py`

## Running tests

```
python -m pytest
```

All tests mock external calls — no real API requests, no quota used.

## Design decisions (and the reasoning behind them)

- **RapidAPI instead of Skyscanner/Booking.com's own APIs** — the official APIs require an approved partner agreement, not open to individual developers. RapidAPI's marketplace hosts third-party wrappers around equivalent data, accessible to anyone.
- **Gemini instead of OpenAI/Anthropic** — free tier with no billing setup, sufficient for portfolio-scale usage. Deliberately pinned to `gemini-flash-lite-latest` rather than the newest release after repeatedly hitting `503` overload errors on newer models — reliability over having the latest model.
- **LangGraph instead of a hand-rolled loop** — the built-in checkpointer is what makes real pause/resume possible (the email-approval step genuinely halts execution mid-graph, not just a UI trick), and conditional edges make the tool-calling loop's control flow explicit and inspectable rather than buried in nested conditionals.
- **A shared `extract_text()` utility** — different Gemini model versions return `response.content` in different shapes (plain string vs. a list of content blocks). Normalizing this in one place, used by every file that calls the LLM, avoids the same bug needing to be fixed independently in multiple places.
- **Retry logic on LLM/API calls** — free-tier LLM APIs have a real transient failure rate (server overload, dropped connections). A lightweight retry decorator (3 attempts, increasing delay) meaningfully improves reliability without over-engineering a full circuit-breaker system.
- **No RAG / vector store** — deliberately scoped out. This app's value is live pricing and availability data, not static destination trivia — grounding via real-time tool calls is the right fit here, retrieval from a fixed knowledge base wouldn't add much.

## Known limitations

- Emails may land in spam without full domain authentication (SPF/DKIM records) — this project uses SendGrid's simpler Single Sender Verification instead of full domain auth.
- Test coverage is at the tool level (`flights_finder`, `hotel_finder`, `itinerary_planner`, shared utils); the LangGraph orchestration logic in `agent.py` itself isn't yet covered by automated tests.
- No caching — identical repeated queries re-hit rate-limited external APIs.
- No deployment yet; runs locally via `streamlit run app.py`.

## Project structure

```
travel_agent/
├── agents/
│   ├── agent.py                 LangGraph orchestrator
│   ├── utils.py                 shared helpers (extract_text, retry_on_failure)
│   └── tools/
│       ├── flights_finder.py
│       ├── hotel_finder.py
│       ├── itinerary_planner.py
│       └── email_sender.py
├── tests/
│   ├── test_flights_finder.py
│   ├── test_hotel_finder.py
│   ├── test_itinerary_planner.py
│   └── test_utils.py
├── app.py                       Streamlit UI
├── requirements.txt
└── .env                         not committed — see .gitignore
```
