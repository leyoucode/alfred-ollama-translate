# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Alfred workflow for offline Chinese-English translation using Ollama (local LLM). Bundle ID: `co.liuwei.alfred.translate.ollama`. All translation runs locally via the Ollama API — no cloud services.

## Architecture

The workflow has two entry points configured in `info.plist`:
- **`ten <text>`** — Chinese → English translation (`/usr/bin/python3 translate.py en {query}`)
- **`tcn <text>`** — English → Chinese translation (`/usr/bin/python3 translate.py cn {query}`)

Both feed into a single Copy to Clipboard output node.

`translate.py` is the sole source file. It calls Ollama's chat API (`http://localhost:11434/api/chat`) with the `qwen2:7b` model, streaming disabled, 30s timeout. Output is Alfred JSON format (`{"items": [...]}`).

The prompt asks the model to return a JSON array of sentence pairs (`[{"src": "...", "tgt": "..."}]`). `parse_sentence_pairs()` parses the response (with regex fallback), and `generate_preview_html()` generates a QuickLook HTML file at `/tmp/alfred_ollama_translate.html` with paired `<span>` elements for click-to-highlight sentence alignment. If the model doesn't return valid JSON, it falls back to plain text display without highlighting.

## Running and Testing

Prerequisites: Ollama running locally with `qwen2:7b` model pulled.

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
