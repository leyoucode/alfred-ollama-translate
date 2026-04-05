#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import sys
import os
import logging
import html
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "demonbyron/HY-MT1.5-7B"

log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")
logging.basicConfig(filename=log_path, level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s %(message)s")


def detect_language(text):
    """If text contains any CJK characters, translate to English; else to Chinese."""
    if re.search(r'[\u4e00-\u9fff\u3400-\u4dbf]', text):
        return 'en'
    return 'cn'


def split_sentences(text):
    """Split text into sentences, handling both Chinese and English."""
    text = text.strip()
    if not text:
        return []
    has_cjk = bool(re.search(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
    if has_cjk:
        parts = re.split(r'(?<=[。！？])', text)
    else:
        parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def build_sentence_pairs(source, translation):
    """Build sentence pairs by splitting source and translation into sentences.
    Returns list of pairs if counts match, else None."""
    src_sents = split_sentences(source)
    tgt_sents = split_sentences(translation)
    if len(src_sents) == len(tgt_sents) and len(src_sents) > 1:
        return [{"src": s, "tgt": t} for s, t in zip(src_sents, tgt_sents)]
    return None


def generate_preview_html(pairs, direction, original=None, translation=None):
    if direction == "en":
        left_label, right_label = "中文原文", "English Translation"
    else:
        left_label, right_label = "English Original", "中文译文"

    if pairs:
        left_parts = []
        right_parts = []
        for i, p in enumerate(pairs):
            left_parts.append(f'<span class="s" data-i="{i}">{html.escape(p["src"])}</span>')
            right_parts.append(f'<span class="s" data-i="{i}">{html.escape(p["tgt"])}</span>')
        left_html = " ".join(left_parts)
        right_html = " ".join(right_parts)
    else:
        left_html = html.escape(original or "")
        right_html = html.escape(translation or "")

    highlight_css = ""
    highlight_js = ""
    if pairs:
        highlight_css = (
            "  .s { cursor: pointer; border-radius: 3px; padding: 1px 2px;"
            " transition: all .25s cubic-bezier(.4,0,.2,1); }\n"
            "  .s:hover { background: rgba(255,255,255,.05); }\n"
            "  .s.active { background: rgba(90,160,255,.22);"
            " box-shadow: inset 0 -2px 0 rgba(90,160,255,.6); }\n"
            "  @media (prefers-color-scheme: light) {\n"
            "    .s:hover { background: rgba(0,0,0,.03); }\n"
            "    .s.active { background: rgba(0,100,220,.14);"
            " box-shadow: inset 0 -2px 0 rgba(0,100,220,.45); }\n"
            "  }\n"
        )
        highlight_js = """
<script>
(function() {
  function clearAll() {
    document.querySelectorAll('.s.active').forEach(function(el) { el.classList.remove('active'); });
  }
  document.querySelectorAll('.s').forEach(function(el) {
    el.addEventListener('click', function(e) {
      e.stopPropagation();
      clearAll();
      var idx = this.dataset.i;
      document.querySelectorAll('.s[data-i="' + idx + '"]').forEach(function(s) { s.classList.add('active'); });
    });
  });
  document.addEventListener('click', clearAll);
})();
</script>"""

    content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
    padding: 28px 32px;
    background: #161618; color: rgba(255,255,255,.84);
  }}
  .wrap {{
    background: rgba(255,255,255,.04);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 0 0 .5px rgba(255,255,255,.08), 0 2px 8px rgba(0,0,0,.35);
    display: flex;
  }}
  .panel {{
    flex: 1; padding: 22px 26px;
  }}
  .panel + .panel {{
    border-left: 1px solid rgba(255,255,255,.06);
  }}
  .label {{
    font-size: 11px; font-weight: 500; letter-spacing: .6px;
    color: rgba(255,255,255,.26);
    text-transform: uppercase; margin-bottom: 14px;
  }}
  .text {{
    font-size: 15px; line-height: 1.82; white-space: pre-wrap;
    word-wrap: break-word;
    color: rgba(255,255,255,.76);
  }}
{highlight_css}
  @media (prefers-color-scheme: light) {{
    body {{ background: #f5f5f7; color: #1d1d1f; }}
    .wrap {{
      background: #fff;
      box-shadow: 0 0 0 .5px rgba(0,0,0,.08), 0 2px 8px rgba(0,0,0,.06);
    }}
    .panel + .panel {{ border-left-color: rgba(0,0,0,.06); }}
    .label {{ color: rgba(0,0,0,.3); }}
    .text {{ color: rgba(0,0,0,.78); }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="panel">
    <div class="label">{left_label}</div>
    <div class="text">{left_html}</div>
  </div>
  <div class="panel">
    <div class="label">{right_label}</div>
    <div class="text">{right_html}</div>
  </div>
</div>
{highlight_js}
</body>
</html>"""

    path = "/tmp/alfred_ollama_translate.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def alfred_output(title, subtitle="", arg="", valid=True, quicklookurl=None, mods=None):
    item = {"title": title, "subtitle": subtitle, "arg": arg, "valid": valid}
    if quicklookurl:
        item["quicklookurl"] = quicklookurl
    if arg:
        item["text"] = {"largetype": arg}
    if mods:
        item["mods"] = mods
    print(json.dumps({"items": [item]}))


def translate(text, direction):
    if direction == "en":
        instruction = "Translate the following segment into English, without additional explanation."
    else:
        instruction = "Translate the following segment into Chinese, without additional explanation."

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": f"{instruction}\n{text}"}
        ],
        "stream": False
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})

    # Bypass proxy for local Ollama requests
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    content = result["message"]["content"].strip()
    logging.debug("model response: %s", content)
    return content


def main():
    logging.debug("argv: %s", sys.argv)

    direction = sys.argv[1] if len(sys.argv) > 1 else "auto"

    if len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
    elif not sys.stdin.isatty():
        query = sys.stdin.read().strip()
    else:
        query = ""

    logging.debug("direction: %s, query: %s", direction, query)

    # Empty query: show direction picker (List Filter UX via autocomplete)
    if not query:
        print(json.dumps({"items": [
            {
                "title": "中译英",
                "subtitle": "按 Tab 选择，然后输入中文",
                "arg": "", "valid": False,
                "autocomplete": "en: "
            },
            {
                "title": "英译中",
                "subtitle": "按 Tab 选择，然后输入英文",
                "arg": "", "valid": False,
                "autocomplete": "cn: "
            }
        ]}))
        return

    # Handle direction prefix (set by autocomplete) or auto-detect
    if direction == "auto":
        if query.startswith("en: "):
            direction = "en"
            query = query[4:]
        elif query.startswith("cn: "):
            direction = "cn"
            query = query[4:]
        else:
            direction = detect_language(query)

    if not query:
        alfred_output("输入要翻译的文字", subtitle="中英互译 (Ollama)", valid=False)
        return

    try:
        result = translate(query, direction)
        pairs = build_sentence_pairs(query, result)
        if pairs:
            translation = " ".join(p["tgt"] for p in pairs)
            preview = generate_preview_html(pairs, direction)
        else:
            translation = result
            preview = generate_preview_html(None, direction, query, translation)
        subtitle = "中→英" if direction == "en" else "英→中"
        tts_arg = f"{direction}:{translation}"
        mods = {"cmd": {"arg": tts_arg, "subtitle": "⌘↩ 朗读", "valid": True}}
        alfred_output(translation, subtitle=f"{subtitle} | Shift 查看对照 | ⌘↩ 朗读",
                      arg=translation, quicklookurl=preview, mods=mods)
    except urllib.error.URLError:
        alfred_output("无法连接 Ollama", subtitle="请确保 Ollama 正在运行", valid=False)
    except TimeoutError:
        alfred_output("翻译超时", subtitle="请稍后重试", valid=False)
    except Exception as e:
        alfred_output(f"错误: {e}", subtitle="翻译失败", valid=False)


if __name__ == "__main__":
    main()
