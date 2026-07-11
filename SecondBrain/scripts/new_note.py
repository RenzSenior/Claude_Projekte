"""
Erstellt eine neue Notiz aus einem Template im Second-Brain-Vault.

Nutzung:
    python new_note.py --type meeting --title "Kickoff Kunde X"
"""
import argparse
import re
import sys
from datetime import date
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent

TYPE_TO_FOLDER = {
    "meeting": "02-meetings",
    "decision": "01-entscheidungen",
    "task": "06-tasks",
    "person": "04-personen",
    "project": "03-projekte",
    "concept": "05-konzepte",
}


def slugify(title: str) -> str:
    slug = title.strip().lower()
    slug = re.sub(r"[^a-z0-9äöüß]+", "-", slug)
    slug = slug.strip("-")
    return slug or "notiz"


def create_note(note_type: str, title: str) -> Path:
    folder = VAULT_ROOT / TYPE_TO_FOLDER[note_type]
    template_path = VAULT_ROOT / "_templates" / f"{note_type}.md"

    if not template_path.exists():
        raise FileNotFoundError(f"Template nicht gefunden: {template_path}")

    folder.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    content = template_path.read_text(encoding="utf-8")
    content = content.replace("{{date}}", today).replace("{{title}}", title)

    filename = f"{today}-{slugify(title)}.md"
    note_path = folder / filename

    if note_path.exists():
        raise FileExistsError(f"Notiz existiert bereits: {note_path}")

    note_path.write_text(content, encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Neue Second-Brain-Notiz anlegen")
    parser.add_argument(
        "--type",
        required=True,
        choices=sorted(TYPE_TO_FOLDER.keys()),
        help="Notiz-Typ",
    )
    parser.add_argument("--title", required=True, help="Titel der Notiz")
    args = parser.parse_args()

    try:
        note_path = create_note(args.type, args.title)
    except (FileNotFoundError, FileExistsError) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Notiz erstellt: {note_path.relative_to(VAULT_ROOT)}")


if __name__ == "__main__":
    main()
