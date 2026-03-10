# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Alfred workflow for offline Chinese-English translation using Ollama (local LLM). Bundle ID: `co.liuwei.alfred.translate.ollama`. All translation runs locally via the Ollama API — no cloud services.

## Architecture

The workflow has two entry points configured in `info.plist`:
- **`ten <text>`** — Chinese → English translation (`/usr/bin/python3 translate.py en {query}`)
- **`tcn <text>`** — English → Chinese translation (`/usr/bin/python3 translate.py cn {query}`)

Both feed into a single Copy to Clipboard output node.

`translate.py` is the sole source file. It calls Ollama's chat API (`http://localhost:11434/api/chat`) with the `demonbyron/HY-MT1.5-7B` model (Tencent Hunyuan MT, WMT25 champion upgrade), streaming disabled, 60s timeout. Output is Alfred JSON format (`{"items": [...]}`).

The prompt uses HY-MT's recommended format: `Translate the following segment into <language>, without additional explanation.` Since HY-MT is a dedicated translation model (not a general chatbot), it returns plain translated text. `split_sentences()` splits both source and translation by punctuation, and `build_sentence_pairs()` pairs them if sentence counts match. `generate_preview_html()` generates a QuickLook HTML file at `/tmp/alfred_ollama_translate.html` with paired `<span>` elements for click-to-highlight sentence alignment. If sentence counts don't match, it falls back to plain text display without highlighting.

## Running and Testing

Prerequisites: Ollama running locally with `demonbyron/HY-MT1.5-7B` model pulled.

```bash
# Test from command line
/usr/bin/python3 translate.py en "你好世界"
/usr/bin/python3 translate.py cn "hello world"
```

Output is Alfred Script Filter JSON. Debug logs go to `debug.log` in the workflow directory.

## Key Configuration

- **Ollama endpoint and model** are constants at the top of `translate.py` (`OLLAMA_URL`, `MODEL`)
- **Workflow triggers, keywords, and UI text** are in `info.plist` (Alfred's XML plist format)
- **Queue mode**: incoming requests queued with 3-second delay to avoid overloading Ollama

## Dependencies

Python 3 standard library only (no pip packages). Requires Ollama service running on localhost:11434.
