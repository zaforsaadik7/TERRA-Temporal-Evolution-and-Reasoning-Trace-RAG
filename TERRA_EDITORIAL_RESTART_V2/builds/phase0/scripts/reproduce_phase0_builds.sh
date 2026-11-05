#!/usr/bin/env bash
# Reproduce Phase 0 diagnostic builds B1-B4 exactly (TeX Live 2023/Debian:
# pdfTeX 1.40.25, XeTeX 0.999995, BibTeX 0.99d; packages texlive-base/-publishers/
# -latex-extra/-science/-pictures/-fonts-recommended/-fonts-extra 2023.20240207-1, cm-super 0.3.4-17).
# Run from TERRA_EDITORIAL_RESTART_V2/. Builds happen in a fresh OUT dir; nothing in working/ is modified.
set -euo pipefail
OUT="${1:?usage: reproduce_phase0_builds.sh OUTPUT_DIR (must not exist)}"
[ -e "$OUT" ] && { echo "OUT exists; choose a new path"; exit 1; }
export SOURCE_DATE_EPOCH=1790467200 FORCE_SOURCE_DATE=1
build () { # name engine
  local d="$OUT/$1"; mkdir -p "$d"; cp -r working/src/. "$d/"; rm -f "$d/main.bbl"
  case "$1" in
    B3_pdflatex_journal) sed -i 's/\\documentclass\[conference\]{IEEEtran}/\\documentclass[journal]{IEEEtran}/' "$d/main.tex";;
    B4_pdflatex_elsevier_casdc) cp builds/phase0/B4_pdflatex_elsevier_casdc/main_B4_ported.tex "$d/main.tex";;
  esac
  ( cd "$d"; $2 -interaction=nonstopmode main.tex; bibtex main; $2 -interaction=nonstopmode main.tex; $2 -interaction=nonstopmode main.tex ) > "$d/stdout.txt" 2>&1 || true
  sha256sum "$d/main.pdf"
}
build B1_provenance_xelatex_conference xelatex
build B2_pdflatex_conference pdflatex
build B3_pdflatex_journal pdflatex
build B4_pdflatex_elsevier_casdc pdflatex
# Expected SHA256: B1 31a70e5b8fb933fc8afed0767f6a793cbac888ab8942610b017914eee1f95cac
#                  B2 78696ef6ec553e6885fd181eac73c5cdf61df6bf3d65dde480afa719fe78fba4
#                  B3 1068d126d21dd0110210c9e793c36774e2d5acf3b5d7f39e2430fcbf6060898e
#                  B4 d98920733e05ff24c17d53b542816e62ddfafea8e9419b0917178c0babb9a99e
