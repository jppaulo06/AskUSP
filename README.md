# AskUSP

A chatbot that answers questions about the **University of São Paulo** using
freshly crawled, up-to-date university data — so answers reflect what's actually
published today rather than what a model happened to memorise.

## How it works

- **Crawling** — [`crawl4ai`](https://github.com/unclecode/crawl4ai) collects and
  cleans content from USP web pages.
- **Storage** — the crawled data is stored in **PostgreSQL**.
- **Answering** — an LLM (**Anthropic Claude**) answers user questions grounded in
  that data, with **[Instructor](https://github.com/jxnl/instructor)** enforcing
  structured, validated outputs.
- **API** — served through **FastAPI**.

## Stack

`Python 3.13` · `FastAPI` · `Anthropic Claude` · `Instructor` · `crawl4ai` ·
`PostgreSQL (psycopg)` · `Pydantic` · `loguru`

## Running

```bash
# Install dependencies (uses uv)
uv sync

# Configure environment (API keys, database URL) in config/
# then start the API
uv run -m app.main
```

## Project layout

```
app/          FastAPI application and entry point
  models/     Data models and LLM response schemas
config/       Settings and environment configuration
database/     Schema and data-access code
```

## Status

An experimental project exploring retrieval-grounded chat over live institutional
data.
