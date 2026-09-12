# Web Chatbot Prototype

This repository contains a web-based chatbot/application prototype with a Python backend, document/data ingestion utilities, and a lightweight browser interface.

## Components

- `app.py` — application/backend logic
- `data_ingestor.py` — data ingestion utilities
- `file_loader.py` — file loading/processing
- `config.py` — application configuration
- `index.html`, `script.js`, `styles.css` — browser interface

## Purpose

The project was used to explore end-to-end integration of a conversational interface with locally loaded data. It is an application prototype rather than a new language-model architecture.

## Development Note

The repository contains several historical copies of earlier scripts. For a production or publication-quality version, those copies should be removed and the application should be organized around a single documented entry point.


## Goal

The application connects local document loading to a browser chat interface and an Ollama-backed language model, providing a compact end-to-end prototype for conversational access to user-supplied files.

## Installation

No dependency manifest is committed. The code imports Flask, CogVault, LangChain's Ollama integration, and Werkzeug, and it requires a separately running Ollama service with the configured model available.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install flask werkzeug cogvault langchain-ollama
python app.py
```

## Working with the Repository

Review model and upload settings in `config.py`, then start Ollama before the Flask application. `data_ingestor.py` and `file_loader.py` handle local content; `index.html` and `script.js` provide the browser client. Do not load confidential documents without first checking where the configured model and embeddings are processed or stored.
