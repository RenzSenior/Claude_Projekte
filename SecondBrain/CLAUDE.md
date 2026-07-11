# Projekt: Persönliches "AI Brain" – Kontext-Graph mit Agent-Zugriff

## Ziel

Aufbau eines persönlichen Wissenssystems ("Second Brain"), auf das KI-Agenten
zugreifen können, um kontextbezogene statt generische Antworten zu liefern.

Vorbild-Architektur (aus einem LinkedIn-Post):
- Alle relevanten Datenquellen (CRM, Meetingtranskripte, Slack, Aufgaben,
  Entscheidungen) werden zentral gesammelt.
- Eine KI sortiert diese Inhalte in einen verlinkten Graphen ein
  (Notizen referenzieren sich gegenseitig, alles durchsuchbar).
- Eigene KI-Agenten greifen auf diesen Graphen zu ("zweites Gehirn") und
  liefern dadurch Antworten, die auf echtem, persönlichem Kontext basieren
  statt auf generischem Weltwissen.

Gewählter Ansatz: **Mittlere Ausbaustufe** – MCP-basierte Anbindung an
bestehende Tools (Obsidian-Vault als Wissensbasis, plus Datenquellen-Connectoren),
mit Perspektive auf einen **agentischen Python-Aufbau** (eigener Retrieval-
Agent, später eigene Automatisierungs-Pipeline).

---

## Architekturüberblick

```
                    ┌─────────────────────────────┐
                    │        Datenquellen          │
                    │  CRM / Slack / Meetings /     │
                    │  Tasks / Mail / Notizen       │
                    └───────────────┬───────────────┘
                                    │ (Ingestion-Skripte)
                                    ▼
                    ┌─────────────────────────────┐
                    │   Obsidian Vault (Markdown)   │
                    │   = Single Source of Truth    │
                    │   - Notizen, verlinkt [[..]]  │
                    │   - Frontmatter (Metadaten)   │
                    └───────────────┬───────────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  ▼                 ▼                 ▼
          ┌───────────────┐ ┌──────────────┐ ┌─────────────────┐
          │  Embeddings /  │ │  MCP Server   │ │  Claude Code /   │
          │  Vektor-Index  │ │ (Dateizugriff)│ │  Claude Desktop  │
          │  (Chroma)      │ │               │ │                  │
          └───────┬────────┘ └───────┬──────┘ └────────┬─────────┘
                  │                  │                  │
                  └──────────────────┼──────────────────┘
                                     ▼
                       ┌─────────────────────────────┐
                       │   Python Retrieval-Agent      │
                       │   - nimmt Anfrage entgegen     │
                       │   - sucht relevante Notizen     │
                       │   - baut Kontext-Prompt         │
                       │   - ruft Claude API auf          │
                       └─────────────────────────────┘
```

---

## Phase 1: Wissensbasis aufsetzen (Obsidian Vault)

**Ziel:** Ein strukturierter, lokaler Markdown-Vault als Fundament.

Ordnerstruktur im Vault (`~/second-brain/`):

```
second-brain/
├── 00-inbox/            # Unsortierte Eingänge, werden regelmäßig verarbeitet
├── 01-entscheidungen/   # Jede wichtige Entscheidung als eigene Notiz
├── 02-meetings/         # Transkripte + Zusammenfassungen
├── 03-projekte/         # Ein Ordner pro Projekt/Kunde
├── 04-personen/         # Ein Profil pro Kontakt/Kollege/Kunde
├── 05-konzepte/         # Wiederkehrende Themen, Frameworks, Learnings
├── 06-tasks/            # Aufgaben, verlinkt zu Projekten/Personen
└── _templates/          # Notiz-Vorlagen mit Frontmatter
```

**Frontmatter-Standard** (wichtig für spätere Filterung/Retrieval):

```yaml
---
type: meeting | decision | task | person | project | concept
date: 2026-07-10
project: [[Projekt-X]]
people: [[Person-A]], [[Person-B]]
tags: [vertrieb, kickoff]
source: fireflies | manual | crm-export | slack
---
```

**Claude Code Aufgabe (Phase 1):**
- Lege die obige Ordnerstruktur unter `~/second-brain/` an.
- Erstelle Templates in `_templates/` für jeden `type`.
- Schreibe ein kleines Python-Skript `scripts/new_note.py`, das per CLI
  (`python new_note.py --type meeting --title "Kickoff Kunde X"`) eine neue
  Notiz aus dem passenden Template erzeugt inkl. korrektem Frontmatter und
  Ablage im richtigen Unterordner.

---

## Phase 2: Datenquellen anbinden (Ingestion)

**Ziel:** Rohdaten automatisiert als Markdown-Notizen in `00-inbox/` ablegen.

Prioritäten (Reihenfolge nach Aufwand/Nutzen):

1. **Meetingtranskripte** – z. B. Fireflies/Fathom/Otter Export via API →
   Python-Skript `scripts/ingest_meetings.py`, das neue Transkripte abruft,
   in Markdown umwandelt und mit Frontmatter versieht.
2. **Tasks/Entscheidungen** – manuell, aber ritualisiert (täglicher Eintrag
   via `new_note.py`).
3. **Slack** – optional später über Slack API, relevante Threads exportieren.
4. **CRM** – optional später über CRM-API/CSV-Export.

**Claude Code Aufgabe (Phase 2):**
- Erstelle `scripts/ingest_meetings.py` als Grundgerüst mit:
  - Konfigurierbarer API-Anbindung (Platzhalter für API-Key in `.env`)
  - Umwandlung Transkript → Markdown-Notiz mit korrektem Frontmatter
  - Ablage in `02-meetings/`
- Nutze `python-dotenv` für Secrets, niemals Keys hart codieren.
- Lege `.env.example` mit den benötigten Variablen an.

---

## Phase 3: Retrieval – Wissen durchsuchbar machen

**Ziel:** Der Agent muss aus tausenden Notizen die *relevanten* finden.

Zwei Bausteine:

### 3a. MCP-Filesystem-Zugriff (schnell startklar)
Claude Code / Claude Desktop kann über einen MCP-Filesystem-Server direkt
auf den Vault-Ordner zugreifen und Notizen lesen/durchsuchen. Das reicht für
den Anfang, ist aber reine Volltextsuche ohne semantisches Verständnis.

### 3b. Vektor-Index für semantische Suche (der eigentliche Hebel)
- Lokale Vektordatenbank: **ChromaDB** (einfach, lokal, kein Server nötig)
- Embedding-Modell: über Anthropic/OpenAI-API oder lokal (z. B. `sentence-transformers`)
- Index wird bei jeder neuen/geänderten Notiz aktualisiert (Watcher)

**Claude Code Aufgabe (Phase 3):**
- Erstelle `scripts/build_index.py`:
  - Liest alle `.md`-Dateien im Vault
  - Chunked lange Notizen sinnvoll (z. B. pro Abschnitt)
  - Erzeugt Embeddings, speichert in ChromaDB unter `.index/`
  - Speichert Metadaten (Pfad, type, date, project) pro Chunk mit
- Erstelle `scripts/watch_vault.py`:
  - Nutzt `watchdog`, um Änderungen im Vault zu erkennen
  - Aktualisiert automatisch nur die geänderten Einträge im Index

---

## Phase 4: Der Agent selbst

**Ziel:** Ein Python-Agent, der bei einer Anfrage:
1. relevante Notizen aus dem Vektor-Index zieht (Top-k Chunks),
2. daraus einen Kontext-Block baut,
3. diesen zusammen mit der eigentlichen Frage an die Claude API schickt,
4. die Antwort zurückgibt – inkl. Quellenangabe (welche Notizen genutzt wurden).

Grundgerüst `agent/context_agent.py`:

```python
"""
Retrieval-Agent: beantwortet Fragen mit persönlichem Kontext aus dem
Second-Brain-Vault.
"""
import os
from dotenv import load_dotenv
import chromadb
import anthropic

load_dotenv()

VAULT_PATH = os.getenv("VAULT_PATH", "~/second-brain")
INDEX_PATH = os.getenv("INDEX_PATH", "./.index")
TOP_K = 6

client = anthropic.Anthropic()  # nutzt ANTHROPIC_API_KEY aus .env
chroma_client = chromadb.PersistentClient(path=INDEX_PATH)
collection = chroma_client.get_or_create_collection("second_brain")


def retrieve_context(query: str, k: int = TOP_K) -> list[dict]:
    """Holt die relevantesten Notiz-Chunks zur Anfrage."""
    results = collection.query(query_texts=[query], n_results=k)
    return [
        {"text": doc, "meta": meta}
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]


def build_prompt(query: str, chunks: list[dict]) -> str:
    context_block = "\n\n---\n\n".join(
        f"Quelle: {c['meta'].get('path')}\n{c['text']}" for c in chunks
    )
    return f"""Du bist mein persönlicher Assistent mit Zugriff auf meinen
Wissens-Vault. Nutze AUSSCHLIESSLICH den folgenden Kontext, um zu antworten.
Wenn der Kontext nicht ausreicht, sag das explizit.

KONTEXT:
{context_block}

FRAGE:
{query}
"""


def ask(query: str) -> str:
    chunks = retrieve_context(query)
    prompt = build_prompt(query, chunks)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


if __name__ == "__main__":
    import sys
    frage = " ".join(sys.argv[1:]) or "Was sind meine offenen Entscheidungen?"
    print(ask(frage))
```

**Claude Code Aufgabe (Phase 4):**
- Erstelle das obige Grundgerüst unter `agent/context_agent.py`.
- Ergänze Fehlerbehandlung (leerer Index, fehlender API-Key).
- Ergänze eine einfache CLI-Schleife (`agent/chat.py`) für interaktives
  Fragen-Stellen im Terminal.
- Optional: FastAPI-Wrapper (`agent/api.py`), um den Agenten später auch
  aus anderen Tools (z. B. einem Chat-Interface) ansprechbar zu machen.

---

## Phase 5: Ausbau (später, nicht sofort)

- Automatische Verlinkung: Ein Skript, das neue Notizen analysiert und
  Vorschläge für `[[Verlinkungen]]` zu bestehenden Notizen macht.
- Wöchentlicher "Review-Agent", der die Inbox durchgeht und Notizen in die
  richtigen Ordner einsortiert + Metadaten ergänzt.
- Eigene MCP-Server-Implementierung, die den Vektor-Index direkt als
  MCP-Tool bereitstellt (statt nur Filesystem-Zugriff), damit Claude
  Desktop/Code direkt semantisch im Vault suchen kann, ohne den
  Python-Agenten separat zu starten.
- Anbindung an CRM/Slack als echte, laufende Automatisierung (z. B. via
  n8n oder Cron-Jobs statt manueller Skript-Aufrufe).

---

## Tech-Stack Zusammenfassung

| Baustein            | Wahl                                  |
|----------------------|----------------------------------------|
| Wissensbasis          | Obsidian Vault (Markdown + Frontmatter)|
| Vektordatenbank        | ChromaDB (lokal)                       |
| Embeddings             | via Anthropic/OpenAI API oder lokal    |
| Agent-Sprache           | Python 3.11+                           |
| LLM                      | Claude (Anthropic API)                 |
| Secrets                  | `.env` + `python-dotenv`               |
| File-Watching             | `watchdog`                             |
| Optional: API-Layer         | FastAPI                                |

---

## Nächste Schritte für Claude Code

1. Lege die Projektstruktur an (siehe Phase 1).
2. Erstelle `requirements.txt` mit: `anthropic`, `chromadb`, `python-dotenv`,
   `watchdog`, `fastapi`, `uvicorn` (letzteres optional/später).
3. Setze Phase 1 + Phase 3a + Phase 4 zuerst um – das ist der schnellste Weg
   zu einem funktionierenden, kontextbasierten Agenten.
4. Phase 2 (Ingestion) und Phase 5 (Ausbau) danach iterativ ergänzen.

**Wichtig:** Bei jedem Schritt zuerst ein Minimal-Setup lauffähig machen und
testen (z. B. 5 Beispielnotizen anlegen, indexieren, eine Testfrage stellen),
bevor die nächste Phase begonnen wird.
