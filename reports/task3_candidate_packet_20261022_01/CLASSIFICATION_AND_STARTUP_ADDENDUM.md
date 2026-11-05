# Inventory classification and startup observations

The preserved `inventory/summary.json` field `external_import_roots` includes four bare module names from relative import statements: bm25_engine, common_serializer, hybrid_retriever and terra_retriever. These are LOCAL modules, not extra installed dependencies. All four are already hashed in repository_code.json and copied in code_checkpoint/. The helper traversed a conservative earlier local closure; this classification error did not remove those files from the inventory. Keep the summary as generated and apply this additive correction when reading it. AST-derived lists remain limited with respect to dynamic imports.

Read-only startup inspection found one top-level venv .pth file: google_generativeai-0.8.6-py3.13-nspkg.pth. Its visible statement imports stdlib namespace machinery and establishes the google namespace; it does not visibly call a model/API client. The file is included in the installed-environment hashes. This is source inspection, not proof about every startup path.

The inspected workspace-root and venv-site-packages sitecustomize.py/usercustomize.py paths, venv/Scripts/python314._pth and base/python314._pth were absent. The venv configuration says include-system-site-packages=false and points home/executable to the measured base runtime. Its historical command records F:\TERRA\venv; it was not rewritten. No startup .pth was executed by the inventory utility (-I -S -B).

An initial PowerShell read-only inspection command had a parser error (an unsupported pipe after foreach). Nothing in that command executed; the corrected read-only command produced the observations above. No process retry or diagnostic attempt occurred.
