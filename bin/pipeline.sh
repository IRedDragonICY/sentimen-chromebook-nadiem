#!/usr/bin/env bash
# Pipeline reproducible end-to-end: data mentah → model → skor penuh.
#
# Pemakaian:
#   MODEL_ANOTATOR=qwen3.5:9b bin/pipeline.sh          # jalankan penuh
#   bin/pipeline.sh skor                                # hanya skor ulang (model sudah ada)
#
# Butuh: .venv (uv), server Ollama hidup dengan GPU (CUDA_VISIBLE_DEVICES=0).
set -euo pipefail
cd "$(dirname "$0")/.."

PY=.venv/bin/python
MODEL_ANOTATOR="${MODEL_ANOTATOR:-qwen3.5:9b}"
TAHAP="${1:-penuh}"

log(){ printf '\n\033[1m[%s] %s\033[0m\n' "$(date +%H:%M:%S)" "$*"; }

if [ "$TAHAP" = "penuh" ]; then
  log "1/6 Bangun dataset terpadu dari 11 CSV"
  $PY -m nadiem_sentimen.build_dataset

  log "2/6 Label silver via $MODEL_ANOTATOR (paling lama)"
  $PY -m nadiem_sentimen.label_silver --model "$MODEL_ANOTATOR"

  log "3/6 Susun train/val/test (group-aware, anti-bocor)"
  $PY -m nadiem_sentimen.assemble_training

  log "4/6 Latih baseline TF-IDF + fine-tune IndoBERT"
  $PY -m nadiem_sentimen.baseline_tfidf
  $PY -m nadiem_sentimen.train

  log "5/6 Evaluasi jujur semua model pada gold test"
  $PY -m nadiem_sentimen.evaluate --llm "$MODEL_ANOTATOR"
fi

log "6/6 Skor seluruh 38.845 komentar untuk aplikasi"
$PY -m nadiem_sentimen.skor_penuh

log "Selesai. Jalankan app: .venv/bin/streamlit run app/app.py"
