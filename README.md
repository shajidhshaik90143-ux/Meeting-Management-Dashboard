# Meeting Management Dashboard

A strong local-first meeting management application built with **Python + Streamlit + SQLite**.

## Features

- Dashboard with KPI cards
- Meeting CRUD
- Meeting status workflow
- Search and filters
- Meeting types
- Agenda and participant management
- Action item management
- Assignee, priority and due-date tracking
- Analytics charts
- JSON backup
- CSV export
- SQLite persistence
- No API keys required

## Project Structure

```text
Meeting Management Dashboard/
├── app.py
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   └── database.py
├── data/
│   └── meetings.db       # created automatically
└── static/
```

## Windows Setup

```powershell
cd "Meeting Management Dashboard"
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## macOS / Linux

```bash
cd "Meeting Management Dashboard"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Notes

The database is generated automatically at:

```text
data/meetings.db
```

Use **Export / Backup** in the sidebar to download JSON and CSV copies of your data.
