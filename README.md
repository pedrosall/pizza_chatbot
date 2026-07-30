# 🍕 PizzaBot — AI-powered Telegram ordering bot

[![Tests](https://github.com/pedrosall/pizza_chatbot/actions/workflows/tests.yml/badge.svg)](https://github.com/pedrosall/pizza_chatbot/actions/workflows/tests.yml)

A Telegram bot that takes real pizza orders through natural conversation, backed by a deterministic state machine, an LLM extraction layer with graceful fallback, persistent storage, and a live admin dashboard.

> 📸 Demo GIF coming soon.

## Why this project exists

This started as a rough prototype during my Master's — my first attempt at building anything with an LLM, with little prompt engineering experience and a lot of trial and error. It got frustrating fast: I was asking a single free-text prompt to run the entire conversation, with no validation, no tests, and no clear boundary between "what the AI decides" and "what the code guarantees."

This is a full rebuild from scratch, with a different philosophy: **the LLM is used only where it earns its place** — extracting structured intent from free text — while the conversation flow itself stays deterministic, testable, and safe to reason about. Every AI call has a rule-based fallback, so the bot degrades gracefully instead of breaking when the model is unavailable or returns something unexpected.

## What it does

- Takes a full pizza order through natural conversation on Telegram — including multiple pizzas, mixed sizes, toppings, and drinks mentioned in a single free-text message ("two large pepperonis and a medium margherita")
- Understands common phrasing variations (size synonyms, casual quantity wording) without needing exact keyword matches
- Answers off-topic questions (menu questions, delivery time, small talk) without breaking the ordering flow
- Validates free-text fields (delivery address, special notes) against both an AI check and a deterministic fallback — including basic protection against prompt-injection-style input in the notes field
- Persists every confirmed order to a database
- Serves a live admin dashboard (order history, revenue, best-selling pizzas)

## Architecture

```
Telegram / Streamlit  (thin I/O layers — no business logic)
        │
        ▼
  Conversation (app/conversation.py)
   deterministic state machine, fully unit-testable,
   knows nothing about Telegram or the database
        │
        ├──▶ AI extraction layer (app/ai_extractor.py)
        │     structured output + validation, always optional
        │
        └──▶ Repository (app/repository.py) ──▶ SQLite (SQLAlchemy)
```

The core design rule throughout the project: **`Conversation` has no I/O.** It takes text in, returns text out. Telegram and Streamlit are both thin adapters on top of it — this is what makes the conversation logic testable without a running bot, and what will make it trivial to add another channel (WhatsApp, a REST API) later without touching the business logic.

## Key design decisions

**LLM extraction with mandatory fallback, never a single point of failure.** Every function that calls Gemini (order extraction, off-topic answers, address/notes validation) returns `None` on *any* failure — no API key, no network, unexpected response — and the caller always has a deterministic rule-based path to fall back to. The bot never breaks because Gemini is down.

**Structured output over free-text parsing.** Instead of asking the model to describe the order in prose and regex-parsing the result, Gemini is given a Pydantic schema (`response_schema`) and returns validated JSON directly. This was the single biggest lesson from the original prototype: unconstrained generation is hard to test and easy to break silently.

**AI where language is genuinely ambiguous, rules where the domain is small and closed.** Pizza/size/quantity extraction from free text uses the LLM, because natural language here is genuinely varied. Drink parsing does not — the catalog is small and closed, so a regex-based split handles "a beer and a coke" just fine, faster and without a network call.

**Order taking follows a real pizzeria phone script**, not an arbitrary form. Researched actual order-taking scripts: the full order is captured first (including multiple pizzas in one message), delivery details (name, address) are asked *last*, and the complete order is read back before final confirmation — mirroring how a human operator catches mistakes before closing a call.

**Free-text fields are treated as an attack surface, not just a UX detail.** Delivery address and order notes are the two fully free-text fields in the flow. Both are validated by an LLM check plus a deterministic fallback (blocklist for address, injection-pattern detection for notes) before being accepted — the notes field in particular is designed with prompt-injection resistance in mind, since user-controlled text that could eventually reach another prompt is a real risk surface in LLM-backed applications.

## Project structure

```
app/
  models.py         domain models (Pydantic) — pizzas, sizes, drinks, cart, order
  catalog.py        business data — prices, ingredients
  conversation.py   the state machine (no I/O, fully unit-tested)
  schemas.py        structured-output contracts for the LLM
  ai_extractor.py   all Gemini calls, each with a safe fallback
  business_info.py  single source of truth for FAQ answers (no hallucinated facts)
  db.py             SQLAlchemy engine/session setup
  db_models.py      ORM table definitions
  repository.py     data access layer (save_order, list_orders)
bot/
  telegram_bot.py   thin aiogram adapter: Telegram messages <-> Conversation
dashboard/
  dashboard_app.py  Streamlit admin dashboard
tests/
  test_conversation.py   state machine tests (mocked AI calls — fast, deterministic)
  test_repository.py     persistence tests (in-memory SQLite)
```

## Running it locally

Clone the repo and set up a virtual environment:

```bash
git clone https://github.com/pedrosall/pizza_chatbot.git
cd pizza_chatbot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

(On Windows PowerShell, activate with `.\venv\Scripts\Activate.ps1` instead.)

Create a `.env` file in the project root with:

```
GEMINI_API_KEY=your_key_here
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

Run the bot:

```bash
python -m bot.telegram_bot
```

Run the dashboard, in a separate terminal:

```bash
PYTHONPATH=. streamlit run dashboard/dashboard_app.py
```

## Running with Docker

```bash
docker compose up
```

This starts both the bot and the dashboard as separate services, sharing the same SQLite database through a named volume. Dashboard available at `http://localhost:8501`.

## Tests & CI

```bash
pytest -v
```

24 tests covering the state machine and the persistence layer. All AI calls are mocked (`unittest.mock.patch`), so the suite is fast, deterministic, and requires no API keys or network access — including in CI, which runs on every push via GitHub Actions.

## What I'd build next

- Persist in-progress conversations (currently in-memory; a restart mid-order loses that specific conversation, though confirmed orders are always safe in the database)
- Order status tracking (received → preparing → out for delivery)
- Postgres for production (the repository layer is already database-agnostic — this is a one-line `DATABASE_URL` change)
- Basic auth on the dashboard before any real deployment

## Stack

Python · aiogram · Streamlit · SQLAlchemy · SQLite · Pydantic · Google Gemini (structured output) · pytest · Docker · GitHub Actions
