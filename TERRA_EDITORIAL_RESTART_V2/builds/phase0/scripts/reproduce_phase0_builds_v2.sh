#!/usr/bin/env bash
# v2 (fail-closed) of reproduce_phase0_builds.sh — supersedes v1 as a PASS/FAIL check (v1 kept unaltered).
# Toolchain: TeX Live 2023/Debian (pdfTeX 1.40.25, XeTeX 0.999995, BibTeX 0.99d; texlive-* 2023.20240207-1, cm-super 0.3.4-17).
# Run from TERRA_EDITORIAL_RESTART_V2/. Builds in a NEW output dir; never writes to working/.
# Exit 0 only if every engine/BibTeX step exits 0 and every PDF SHA256 equals the expected value.
set -euo pipefail
OUT="${1:?usage: reproduce_phase0_builds_v2.sh OUTPUT_DIR (must not exist)}"
[ -e "$OUT" ] && { echo "FAIL: $OUT exists"; exit 2; }
export SOURCE_DATE_EPOCH=1790467200 FORCE_SOURCE_DATE=1
declare -A EXPECT=(
 [B1_provenance_xelatex_conference]=31a70e5b8fb933fc8afed0767f6a793cbac888ab8942610b017914eee1f95cac
 [B2_pdflatex_conference]=78696ef6ec553e6885fd181eac73c5cdf61df6bf3d65dde480afa719fe78fba4
 [B3_pdflatex_journal]=1068d126d21dd0110210c9e793c36774e2d5acf3b5d7f39e2430fcbf6060898e
 [B4_pdflatex_elsevier_casdc]=d98920733e05ff24c17d53b542816e62ddfafea8e9419b0917178c0babb9a99e )
fail=0
build () { # name engine
  local d="$OUT/$1" rc=0; mkdir -p "$d"; cp -r working/src/. "$d/"; rm -f "$d/main.bbl"
  case "$1" in
    B3_pdflatex_journal) sed -i 's/\\documentclass\[conference\]{IEEEtran}/\\documentclass[journal]{IEEEtran}/' "$d/main.tex";;
    B4_pdflatex_elsevier_casdc) cp builds/phase0/B4_pdflatex_elsevier_casdc/main_B4_ported.tex "$d/main.tex";;
  esac
  ( cd "$d" && $2 -interaction=nonstopmode -halt-on-error main.tex && bibtex main && \
    $2 -interaction=nonstopmode -halt-on-error main.tex && $2 -interaction=nonstopmode -halt-on-error main.tex ) \
    > "$d/stdout.txt" 2>&1 || rc=$?
  if [ $rc -ne 0 ] || [ ! -f "$d/main.pdf" ]; then echo "FAIL $1: build exit $rc (see $d/stdout.txt)"; fail=1; return 0; fi
  local h; h=$(sha256sum "$d/main.pdf" | cut -d' ' -f1)
  if [ "$h" = "${EXPECT[$1]}" ]; then echo "PASS $1 $h"; else echo "FAIL $1: got $h expected ${EXPECT[$1]}"; fail=1; fi
}
build B1_provenance_xelatex_conference xelatex
build B2_pdflatex_conference pdflatex
build B3_pdflatex_journal pdflatex
build B4_pdflatex_elsevier_casdc pdflatex
[ $fail -eq 0 ] && echo "ALL PASS" || { echo "OVERALL FAIL"; exit 1; }
