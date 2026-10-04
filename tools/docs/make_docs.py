"""Rebuild docs/All_For_One_Code_Guide.pdf from the current code.

    pip install -r requirements-dev.txt      (once)
    python tools/docs/make_docs.py

Steps: shots.py takes screenshots and records physics data (no window opens),
figures.py draws the diagrams, build_pdf.py writes the PDF using the text in
content.py. Working files go to docs/_build/ (not in git).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BUILD = os.path.join(ROOT, "docs", "_build")
PDF = os.path.join(ROOT, "docs", "All_For_One_Code_Guide.pdf")

if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True)
    for script, args in (("shots.py", [BUILD]), ("figures.py", [BUILD]), ("build_pdf.py", [BUILD, PDF])):
        print(f"--- {script}")
        subprocess.run([sys.executable, os.path.join(HERE, script), *args], cwd=ROOT, check=True)
    print("PDF written to", PDF)
