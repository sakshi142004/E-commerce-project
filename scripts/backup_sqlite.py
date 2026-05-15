import shutil
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE_DB = BASE_DIR / "instance" / "site.db"
BACKUP_DIR = BASE_DIR / "backups"


def main():
    if not SOURCE_DB.exists():
        raise SystemExit(f"SQLite database not found: {SOURCE_DB}")

    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"site_backup_{timestamp}.db"
    shutil.copy2(SOURCE_DB, backup_path)
    print(f"Backup created: {backup_path}")


if __name__ == "__main__":
    main()
