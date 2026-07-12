#!/usr/bin/env bash
# Kelanjutan pipeline SETELAH silver labeling selesai:
# tunggu silver.parquet → susun split → baseline → fine-tune → evaluasi → skor.
# Dirancang untuk berjalan tanpa pengawasan (mis. semalam).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
MODEL_ANOTATOR="${MODEL_ANOTATOR:-ornith:9b}"
# Latih & skor di GPU (torch hanya melihat CUDA bila var ini diset).
export CUDA_VISIBLE_DEVICES=0
log(){ printf '\n\033[1m[%s] %s\033[0m\n' "$(date +%H:%M:%S)" "$*"; }

log "Menunggu data/labels/silver.parquet …"
until [ -f data/labels/silver.parquet ]; do sleep 30; done
log "silver.parquet terdeteksi."

log "1/5 Susun train/val/test (group-aware)"
$PY -m nadiem_sentimen.assemble_training

log "2/5 Baseline TF-IDF"
$PY -m nadiem_sentimen.baseline_tfidf

log "3/5 Bebaskan GPU dari anotator, lalu fine-tune IndoBERT"
ollama stop "$MODEL_ANOTATOR" 2>/dev/null || true
sleep 3
$PY -m nadiem_sentimen.train

log "4/5 Evaluasi jujur (majority, TF-IDF, fine-tune) pada gold test"
# Baseline LLM dijalankan terpisah setelah pipeline agar GPU tak berebut
# (ornith + IndoBERT bersamaan melebihi 5,6 GB VRAM).
$PY -m nadiem_sentimen.evaluate

log "5/6 Skor seluruh 38.845 komentar untuk aplikasi"
$PY -m nadiem_sentimen.skor_penuh

log "6/6 Hitung temuan produk + isi metrik nyata ke dokumen"
$PY -m nadiem_sentimen.temuan
$PY bin/isi_dokumen.py

log "PIPELINE SELESAI. Artefak: models/sentimen-id/, reports/{evaluasi,temuan}.json, data/processed/skor.parquet"
