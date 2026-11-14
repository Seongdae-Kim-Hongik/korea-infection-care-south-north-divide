#!/bin/bash
# run_all_asap.sh — 감염성·기생충성 질환 진료 Applied Spatial Analysis and Policy 전체 빌드(2026-11-14). 네트워크 접근 없음.
set -e; cd "$(dirname "$0")"
python3 figs_infect.py 2>&1 | grep -v Warning || true
python3 build_asap_infect.py
python3 esm_infect.py
python3 sanitize_docx.py ../out/Manuscript.docx ../out/ESM_1.docx
