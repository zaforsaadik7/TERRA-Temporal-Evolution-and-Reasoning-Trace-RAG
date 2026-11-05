# Reproduce (sandbox; TeX Live 2023/Debian, pdfTeX 1.40.25, XeTeX same distro, BibTeX 0.99d)
Input: byte copy of CANONICAL_ARCHIVE/src (22-file closure listed in evidence_claude-0003/build_identities.txt); delete main.bbl first.
pdfLaTeX: pdflatex -interaction=nonstopmode main.tex; bibtex main; pdflatex ...; pdflatex ...   -> rebuild_pdflatex_37p.pdf
XeLaTeX : same with xelatex                                                                     -> rebuild_xelatex_39p.pdf
No-hacks: pdfLaTeX on main.tex modified exactly per nohacks_source.diff (removes 4x \enlargethispage, @fptop/@dblfptop override, 5pt bibliography font + itemsep) -> rebuild_pdflatex_nohacks_37p.pdf
All outputs are diagnostics only; none is a proposed baseline.
Note: the sandbox script also normalized CRLF->LF line endings in the no-hacks variant; the diff above ignores that whitespace-only change.
