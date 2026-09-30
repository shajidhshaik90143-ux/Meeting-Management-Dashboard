from src.database import init_db, add_meeting, add_action_item
from datetime import date, timedelta

init_db()

meetings = [
    {
        "title":"Weekly Engineering Sync","organizer":"Engineering Team",
        "meeting_date":str(date.today()+timedelta(days=1)),
        "start_time":"10:00:00","end_time":"11:00:00","meeting_type":"Team",
        "location":"Google Meet","participants":"Engineering, QA",
        "description":"Weekly delivery and blocker review.",
        "agenda":"1. Sprint progress\n2. Blockers\n3. Next sprint priorities",
        "status":"Scheduled"
    },
    {
        "title":"Project Alpha Review","organizer":"Project Manager",
        "meeting_date":str(date.today()+timedelta(days=3)),
        "start_time":"14:00:00","end_time":"15:00:00","meeting_type":"Project",
        "location":"Conference Room A","participants":"PM, Dev, Client",
        "description":"Review milestone completion and risks.",
        "agenda":"1. Demo\n2. Risks\n3. Decisions",
        "status":"Scheduled"
    },
    {
        "title":"Client Discovery","organizer":"Sales Team",
        "meeting_date":str(date.today()-timedelta(days=2)),
        "start_time":"11:00:00","end_time":"12:00:00","meeting_type":"Client",
        "location":"Online","participants":"Sales, Client",
        "description":"Discovery session for requirements.",
        "agenda":"1. Business goals\n2. Requirements\n3. Timeline",
        "status":"Completed"
    }
]

for m in meetings:
    mid = add_meeting(m)
    if m["title"] != "Client Discovery":
        add_action_item({
            "title":"Send meeting summary",
            "assignee":"Project Manager",
            "priority":"High",
            "due_date":str(date.today()+timedelta(days=2)),
            "meeting_id":mid,
            "notes":"Share decisions and next steps.",
            "status":"Open"
        })

print("Demo data inserted.")
