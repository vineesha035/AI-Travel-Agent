# AI Travel Agent — Build Progress & Reference

Rebuilt from scratch (not the original uploaded scaffold). Stack: Python 3.13, conda env `travel-agent`, LangGraph + LangChain, Google Gemini (free tier), RapidAPI (Skyscanner Flights + Booking COM), SendGrid, Streamlit.

## Done

**Stage 1 — API keys.** `.env` (git-ignored) holds `GOOGLE_API_KEY` (aistudio.google.com, free), `RAPIDAPI_KEY` (one key, subscribed to two separate APIs: "Skyscanner Flights" by Crawlio and "Booking COM" by DataCrawler), `SENDGRID_API_KEY` (Single Sender Verification used, no domain needed).

**Stage 2 — Environment.** Conda env `travel-agent` (Python 3.13), isolated from `base`. `requirements.txt` built incrementally, one package per stage as needed, not all upfront.

**Stage 3 — `agents/tools/flights_finder.py`.** Calls Skyscanner Flights API (host `skyscanner-flights4.p.rapidapi.com`). Round-trip endpoint (`/api/v1/roundtrip`) if `return_date` given, else one-way (`/api/v1/search`). `requests.get(..., timeout=15)` — always set timeouts, default is to hang forever.

**Stage 4 — `agents/tools/hotel_finder.py`.** Booking COM API (host `booking-com15.p.rapidapi.com`). Two-step: `_resolve_destination()` calls `searchDestination` to turn a city name into `dest_id`/`search_type`, then `hotels_finder()` calls `searchHotels` with those. Real APIs often need a lookup step before the "real" call — don't assume a free-text field will just work.

**Stage 5 — `agents/tools/itinerary_planner.py`.** First direct LLM call, via `ChatGoogleGenerativeAI`. Model pinned to `gemini-flash-lite-latest` (least contended free-tier model; avoid the newest release for reliability). Key lesson: newer Gemini versions return `response.content` as a list of content blocks, not a plain string — normalized via a shared helper.

**Stage 6 — `agents/agent.py`.** The LangGraph orchestrator.
- `AgentState` — `TypedDict` with `messages: Annotated[list[AnyMessage], operator.add]`. The `operator.add` reducer makes node updates *append* to message history instead of replacing it — without it, every node run wipes prior conversation.
- Loop: `call_tools_llm` (ask the LLM) → `exists_action` (checks if the LLM's last message has `tool_calls`) → if yes, `invoke_tools` (actually run the Python function) → back to `call_tools_llm`. Loops until the LLM responds with no tool call.
- `MemorySaver()` checkpointer, keyed by `thread_id`, enables pause/resume (needed for Stage 8).
- `agents/utils.py` — shared `extract_text()` helper (handles the list-of-blocks response shape), used by `itinerary_planner.py`, `agent.py`, and `app.py`.

**Stage 7 — `app.py`.** Streamlit UI. Key concept: Streamlit reruns the *entire script* on every interaction, so anything that must survive a rerun (the `Agent` instance, `thread_id`) lives in `st.session_state`, guarded by `if "x" not in st.session_state`. Verified working end-to-end through the actual browser: real flights, real hotel, full itinerary.

**Stage 8 — SendGrid email + LangGraph interrupt (done).**
- `agents/tools/email_sender.py` — plain function using `SendGridAPIClient`/`Mail` to send the itinerary as HTML email. Not LLM-callable; we decide when to call it, not the model.
- `agent.py` updated: new node `request_email_decision` runs after the LLM is done calling tools (instead of going straight to `END`). It calls `interrupt({"itinerary": itinerary_text})`, which pauses the entire graph and hands that payload back to the caller. Resuming later with `graph.invoke(Command(resume={...}), config=...)` (same `thread_id`) continues execution from that exact point — either sends the email or skips it, then reaches `END`.
- Confirmed working standalone: `python -m agents.agent` pauses correctly, prints the itinerary from the interrupt payload, resumes with `Command(resume=...)`, and reaches `END`.
- `app.py` updated: `process_query` detects `"__interrupt__"` and stores the itinerary + pause state in `st.session_state`; `render_email_decision` shows the radio + form and resumes the graph via `Command(resume=...)` on the same `thread_id`.
- **Verified fully working end-to-end through the browser**: decline path resumes silently, send path actually delivers a real email via SendGrid (landed in spam initially — expected/normal for a fresh sender without full domain authentication, not a bug).
- Known cosmetic bug to fix in Stage 9: `render_email_decision` shows `st.success()` (green box) even when the email actually fails to send — should branch on whether the note says "sent" vs "failed."

**Stage 9 — Error handling (done).** Added `retry_on_failure` (retry decorator, 3 attempts, increasing delay) in `agents/utils.py`, applied to both LLM calls (`itinerary_planner.py`'s `_call_llm`, `agent.py`'s `_invoke_llm`). Added `try/except requests.exceptions.RequestException` around all 3 `requests.get()` calls (flights, hotel destination lookup, hotel search) so network failures return a clean error dict instead of crashing the whole graph. Fixed `app.py` bug where email failures showed a green success box — now branches on message content.

**Stage 10 — Tests (done).** `tests/` folder, 13 `pytest` tests across 4 files, all mocked (no real API calls, no quota burned). Covers: flights round-trip vs one-way endpoint selection, non-200 responses, network errors; hotel destination resolution success/no-match, error propagation, network errors; itinerary planner success and repeated-failure handling; `retry_on_failure` and `extract_text` utils directly. Run via `python -m pytest` (not bare `pytest` — same import-path reasoning as `python -m agents.agent`). All 13 passing.

**Stage 11 — README (done).** Full `README.md` at project root: features, architecture diagram, tech stack, setup steps, test-running instructions, design-decision talking points, known limitations, project structure.

**Stage 12 — Final verification + deployment (done).** Verified full end-to-end flow locally and in production with multiple fresh queries (Paris, Tokyo, Barcelona) — real flights, real hotels, generated itinerary, both email decline and send paths. Deployed to Streamlit Community Cloud at **https://ai-travel-agent-kz93ftenhqqxtmu3iwxnwu.streamlit.app**, secrets configured via Streamlit Cloud's Secrets manager (TOML format, root-level keys — these are also exposed via `os.environ`, so no code changes were needed versus local `.env`).

## Project status: COMPLETE

All 12 stages done. Working local app, working deployed app, pushed GitHub repo, README, tests, error handling.

## Common bugs hit this session (so you recognize them fast)

- **Indentation mismatches** — by far the most frequent issue. A `def` block, an `if __name__ == "__main__":` block, or a decorator ending up nested one level too deep (inside a class or another function) instead of at the intended level. Symptoms vary: `SyntaxError`, `NameError` (referencing a class before it's fully defined), or a function silently placed after a `return` (dead code, never runs, no error at all).
- **Manual refactors dropping/renaming variables** — e.g. `timeout=15` added by copying a pattern from a different file, introducing a reference to a variable (`endpoint`, `params`) that doesn't exist in that function's scope.
- **Gemini model deprecation/overload** — `gemini-2.5-flash` returned `404` (deprecated for new users); newest releases (`gemini-3.7-flash`) returned frequent `503` (overloaded). Settled on `gemini-flash-lite-latest` for reliability.
- **No timeout on `requests.get()`** — caused a silent hang with no error. Fixed by adding `timeout=15` everywhere.
- **Running a file two different ways changes its imports** — `python agents/agent.py` fails on internal package imports (`agents.tools...`); `python -m agents.agent` from the project root works, because `-m` adds the project root to the import path.

## Key running commands

```
conda activate travel-agent
python -m agents.agent          # test the graph directly
streamlit run app.py            # run the UI
git add . && git status && git commit -m "..." && git push   # always check git status before AND after `add` — confirm .env never appears
```
