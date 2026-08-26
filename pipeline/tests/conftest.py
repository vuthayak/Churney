import sys
from pathlib import Path

# Make the churney/ and scrapers/ packages importable without installing the project.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
