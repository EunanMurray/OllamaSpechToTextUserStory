# Voice to User Story

Speak a feature idea and turn it into a structured user story using local speech-to-text (faster-whisper) and a local LLM (Ollama / llama3.2).

## Requirements

- Python 3.10
- [Ollama](https://ollama.com) running locally with the `llama3.2` model:
  ```
  ollama pull llama3.2
  ```
- A working microphone

## Setup

From the project folder:

```powershell
# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install faster-whisper sounddevice numpy scipy requests
```

## Running

Make sure Ollama is running first, then choose one of the two frontends.

### Web app (recommended)

```powershell
.\.venv\Scripts\python.exe server.py
```

Open <http://127.0.0.1:8000> in your browser.

1. **Speak** — press start, talk, press stop
2. **Transcript** — review or edit the transcribed text
3. **User Story** — generate, then copy any section

### Terminal app

```powershell
.\.venv\Scripts\python.exe main.py
```

Press ENTER to start recording, ENTER again to stop. The terminal version also asks clarifying questions before generating the story.

## Files

- `server.py` — web server (stdlib only)
- `index.html` — web frontend
- `main.py` — terminal app
- `stt.py` — microphone capture + transcription
- `llm.py` — Ollama prompt and API call
- `config.py` — model names and settings
