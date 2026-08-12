#!/usr/bin/env bash
# Copies the canonical reference content from claude-plugin/ (the source of
# truth) into the chatgpt/ and openwebui/ knowledge folders, so all three
# platform packages stay byte-identical on the shared material instead of
# drifting via hand-edited copies. Run this after editing anything under
# claude-plugin/skills/melodrama-script-intelligence/reference/.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

SRC="claude-plugin/skills/melodrama-script-intelligence/reference"

# ChatGPT gets everything, including the HTML template (Code Interpreter
# can fill it in and hand back a real downloadable file).
if [ -d chatgpt/knowledge ]; then
  cp "$SRC"/*.md "$SRC"/*.html chatgpt/knowledge/
  echo "synced -> chatgpt/knowledge"
fi

# OpenWebUI's Knowledge collections run everything through RAG/embedding --
# review-report-template.html is a CSS/JS template with almost no plain
# text once tags are stripped, and its ingestion 400s with "content
# provided is empty" (confirmed against a live instance). It isn't useful
# for semantic retrieval anyway -- only the .md reference docs go here.
if [ -d openwebui/knowledge ]; then
  cp "$SRC"/*.md openwebui/knowledge/
  echo "synced -> openwebui/knowledge (excluding .html -- see comment above)"
fi
