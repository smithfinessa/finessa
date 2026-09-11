from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from db import init_db
from seed import seed


def main():
    init_db()
    seed()
    print("Finessa database initialized.")


if __name__ == "__main__":
    main()
