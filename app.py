"""
CAPABL Recruitment Intelligence OS - Root Application Entry Point.
Delegates directly to capabl_core.ui.app.main() to support running:
    streamlit run app.py
from the repository root.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from capabl_core.ui.app import main

if __name__ == "__main__":
    main()
