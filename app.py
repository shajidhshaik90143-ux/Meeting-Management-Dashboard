import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
from pathlib import Path
import json

from src.database import (
    init_db, get_meetings, add_meeting, update_meeting, delete_meeting,
    get_action_items, add_action_item, update_action_item, delete_action_item,
    get_stats, get_meeting, export_data
)

st.set_page_config(
    page_title="Meeting Management Dashboard",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

# ---------- Styling ----------
st.markdown("""
<style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    .hero {
        padding: 1.4rem 1.6rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #111827, #1f2937);
        color: white;
        margin-bottom: 1.2rem;
    }
    .hero h1 {margin: 0; font-size: 2.1rem;}
    .hero p {margin: .4rem 0 0; color: #d1d5db;}
    .metric-card {
        padding: 1rem;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        background: white;
        min-height: 110px;
    }
    .metric-label {color:#6b7280;font-size:.85rem;}
    .metric-value {font-size:1.75rem;font-weight:700;margin-top:.25rem;}
    .status {
        display:inline-block;padding:.2rem .6rem;border-radius:999px;
        font-size:.75rem;font-weight:600;
    }
    .status-scheduled {background:#dbeafe;color:#1d4ed8;}
    .status-completed {background:#dcfce7;color:#15803d;}
    .status-cancelled {background:#fee2e2;color:#b91c1c;}
    .status-in-progress {background:#fef3c7;color:#b45309;}
    .small-muted {color:#6b7280;font-size:.8rem;}
    div[data-testid="stMetric"] {
        border: 1px solid #e5e7eb; padding: 12px; border-radius: 14px;
        background: white;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>📅 Meeting Management Dashboard</h1>
  <p>Plan meetings, manage agendas, assign action items, and track meeting performance in one place.</p>
</div>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Dashboard", "Meetings", "Action Items", "Analytics", "Export / Backup"],
    index=0
)

st.sidebar.divider()
st.sidebar.caption("Local-first project • SQLite database • No external API required")

# ---------- Helpers ----------
def status_badge(status):
    cls = status.lower().replace(" ", "-")
    return f'<span class="status status-{cls}">{status}</span>'

def safe_df(rows):
    return pd.DataFrame(rows) if rows else pd.DataFrame()

# ---------- Dashboard ----------
if page == "Dashboard":
    stats = get_stats()
    cols = st.columns(5)
    cards = [
        ("Total Meetings", stats["total"]),
        ("Upcoming", stats["upcoming"]),
        ("Completed", stats["completed"]),
        ("Action Items", stats["actions"]),
        ("Open Actions", stats["open_actions"]),
    ]
    for col, (label, value) in zip(cols, cards):
        with col:
            st.metric(label, value)

    st.subheader("Upcoming Meetings")
    upcoming = get_meetings(status="Scheduled", upcoming_only=True, limit=8)
    if upcoming:
        for m in upcoming:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2.6, 1.4, 1.5, 1])
                c1.markdown(f"**{m['title']}**")
                c1.caption(f"{m['meeting_type']} • {m['organizer']}")
                c2.write(f"📅 {m['meeting_date']}")
                c3.write(f"🕐 {m['start_time']} – {m['end_time']}")
                c4.markdown(status_badge(m["status"]), unsafe_allow_html=True)
    else:
        st.info("No upcoming scheduled meetings.")

    st.subheader("Open Action Items")
    actions = get_action_items(status="Open", limit=8)
    if actions:
        adf = safe_df(actions)
        st.dataframe(
            adf[["title", "assignee", "priority", "due_date", "meeting_title"]],
            use_container_width=True, hide_index=True
        )
    else:
        st.success("No open action items.")

# ---------- Meetings ----------
elif page == "Meetings":
    tab1, tab2 = st.tabs(["📋 Meeting List", "➕ Create Meeting"])

    with tab1:
        c1, c2, c3, c4 = st.columns([2, 1.2, 1.2, 1.2])
        search = c1.text_input("Search", placeholder="Title, organizer, location...")
        status_filter = c2.selectbox("Status", ["All", "Scheduled", "In Progress", "Completed", "Cancelled"])
        type_filter = c3.selectbox("Type", ["All", "Team", "Client", "Project", "Interview", "Review", "Other"])
        sort_by = c4.selectbox("Sort", ["Date ↑", "Date ↓", "Title A-Z"])

        meetings = get_meetings(
            search=search,
            status=None if status_filter == "All" else status_filter,
            meeting_type=None if type_filter == "All" else type_filter,
            limit=200
        )
        if sort_by == "Date ↓":
            meetings = sorted(meetings, key=lambda x: (x["meeting_date"], x["start_time"]), reverse=True)
        elif sort_by == "Title A-Z":
            meetings = sorted(meetings, key=lambda x: x["title"].lower())

        if not meetings:
            st.info("No meetings found.")
        else:
            for m in meetings:
                with st.container(border=True):
                    a, b, c, d, e = st.columns([2.5, 1.3, 1.5, 1.3, .8])
                    a.markdown(f"**{m['title']}**")
                    a.caption(f"{m['meeting_type']} • {m['organizer']} • {m['location'] or 'Online'}")
                    b.write(f"📅 {m['meeting_date']}")
                    c.write(f"🕐 {m['start_time']}–{m['end_time']}")
                    d.markdown(status_badge(m["status"]), unsafe_allow_html=True)
                    if e.button("Open", key=f"open_{m['id']}"):
                        st.session_state["selected_meeting"] = m["id"]
                        st.rerun()

            selected = st.session_state.get("selected_meeting")
            if selected:
                m = get_meeting(selected)
                if m:
                    st.divider()
                    st.subheader(f"Meeting Details — {m['title']}")
                    st.write(m.get("description") or "No description.")
                    st.markdown(f"**Agenda**")
                    st.write(m.get("agenda") or "No agenda added.")
                    st.markdown(f"**Participants:** {m.get('participants') or 'Not specified'}")

                    ec1, ec2, ec3 = st.columns(3)
                    with ec1:
                        new_status = st.selectbox(
                            "Update status",
                            ["Scheduled", "In Progress", "Completed", "Cancelled"],
                            index=["Scheduled","In Progress","Completed","Cancelled"].index(m["status"]),
                            key=f"status_{m['id']}"
                        )
                    with ec2:
                        if st.button("Save Status", key=f"save_status_{m['id']}"):
                            update_meeting(m["id"], {"status": new_status})
                            st.success("Status updated.")
                            st.rerun()
                    with ec3:
                        if st.button("Delete Meeting", key=f"delete_{m['id']}"):
                            delete_meeting(m["id"])
                            st.session_state.pop("selected_meeting", None)
                            st.success("Meeting deleted.")
                            st.rerun()

                    st.markdown("### Edit Meeting")
                    with st.form(f"edit_form_{m['id']}"):
                        r1, r2 = st.columns(2)
                        title = r1.text_input("Title", value=m["title"])
                        organizer = r2.text_input("Organizer", value=m["organizer"])
                        r3, r4, r5 = st.columns(3)
                        meeting_date = r3.date_input("Date", value=date.fromisoformat(m["meeting_date"]))
                        start = r4.time_input("Start", value=time.fromisoformat(m["start_time"]))
                        end = r5.time_input("End", value=time.fromisoformat(m["end_time"]))
                        r6, r7 = st.columns(2)
                        meeting_type = r6.selectbox("Type", ["Team","Client","Project","Interview","Review","Other"],
                            index=["Team","Client","Project","Interview","Review","Other"].index(m["meeting_type"]))
                        location = r7.text_input("Location / Link", value=m["location"] or "")
                        participants = st.text_input("Participants", value=m["participants"] or "")
                        description = st.text_area("Description", value=m["description"] or "")
                        agenda = st.text_area("Agenda", value=m["agenda"] or "")
                        if st.form_submit_button("Save Changes", type="primary"):
                            update_meeting(m["id"], {
                                "title": title, "organizer": organizer, "meeting_date": str(meeting_date),
                                "start_time": str(start), "end_time": str(end),
                                "meeting_type": meeting_type, "location": location,
                                "participants": participants, "description": description, "agenda": agenda
                            })
                            st.success("Meeting updated.")
                            st.rerun()

    with tab2:
        with st.form("create_meeting", clear_on_submit=True):
            st.subheader("Create a New Meeting")
            r1, r2 = st.columns(2)
            title = r1.text_input("Meeting Title *")
            organizer = r2.text_input("Organizer *")
            r3, r4, r5 = st.columns(3)
            meeting_date = r3.date_input("Date", value=date.today())
            start = r4.time_input("Start Time", value=time(10, 0))
            end = r5.time_input("End Time", value=time(11, 0))
            r6, r7 = st.columns(2)
            meeting_type = r6.selectbox("Meeting Type", ["Team","Client","Project","Interview","Review","Other"])
            location = r7.text_input("Location / Meeting Link")
            participants = st.text_input("Participants", placeholder="Names separated by commas")
            description = st.text_area("Description")
            agenda = st.text_area("Agenda", placeholder="1. Topic...\n2. Discussion...\n3. Decisions...")
            submitted = st.form_submit_button("Create Meeting", type="primary")
            if submitted:
                if not title.strip() or not organizer.strip():
                    st.error("Title and organizer are required.")
                elif end <= start:
                    st.error("End time must be after start time.")
                else:
                    add_meeting({
                        "title": title.strip(), "organizer": organizer.strip(),
                        "meeting_date": str(meeting_date), "start_time": str(start),
                        "end_time": str(end), "meeting_type": meeting_type,
                        "location": location.strip(), "participants": participants.strip(),
                        "description": description.strip(), "agenda": agenda.strip(),
                        "status": "Scheduled"
                    })
                    st.success("Meeting created successfully.")

# ---------- Action Items ----------
elif page == "Action Items":
    tab1, tab2 = st.tabs(["📌 Action Item Board", "➕ Add Action Item"])
    with tab1:
        status = st.selectbox("Filter status", ["All", "Open", "In Progress", "Completed"])
        actions = get_action_items(status=None if status == "All" else status, limit=500)
        if not actions:
            st.info("No action items.")
        else:
            for a in actions:
                with st.container(border=True):
                    c1, c2, c3, c4, c5 = st.columns([2.6, 1.3, 1.2, 1.2, 1])
                    c1.markdown(f"**{a['title']}**")
                    c1.caption(a["meeting_title"] or "General")
                    c2.write(a["assignee"])
                    c3.write(a["priority"])
                    c4.write(a["due_date"])
                    new_status = c5.selectbox(
                        "Status", ["Open","In Progress","Completed"],
                        index=["Open","In Progress","Completed"].index(a["status"]),
                        key=f"action_status_{a['id']}"
                    )
                    if new_status != a["status"]:
                        update_action_item(a["id"], {"status": new_status})
                        st.rerun()
                    if a.get("notes"):
                        st.caption(a["notes"])

                    x1, x2 = st.columns([1, 1])
                    with x1:
                        if st.button("Delete", key=f"del_action_{a['id']}"):
                            delete_action_item(a["id"])
                            st.rerun()

    with tab2:
        meetings = get_meetings(limit=500)
        meeting_options = {f"{m['title']} ({m['meeting_date']})": m["id"] for m in meetings}
        with st.form("add_action"):
            title = st.text_input("Action Item *")
            assignee = st.text_input("Assignee *")
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            due_date = st.date_input("Due Date", value=date.today())
            meeting_label = st.selectbox("Related Meeting", ["None"] + list(meeting_options.keys()))
            notes = st.text_area("Notes")
            if st.form_submit_button("Add Action Item", type="primary"):
                if not title.strip() or not assignee.strip():
                    st.error("Action item and assignee are required.")
                else:
                    meeting_id = None if meeting_label == "None" else meeting_options[meeting_label]
                    add_action_item({
                        "title": title.strip(), "assignee": assignee.strip(),
                        "priority": priority, "due_date": str(due_date),
                        "meeting_id": meeting_id, "notes": notes.strip(),
                        "status": "Open"
                    })
                    st.success("Action item added.")

# ---------- Analytics ----------
elif page == "Analytics":
    st.subheader("Meeting Analytics")
    meetings = get_meetings(limit=1000)
    actions = get_action_items(limit=1000)
    if not meetings:
        st.info("Create meetings to populate analytics.")
    else:
        df = pd.DataFrame(meetings)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Meetings by Status")
            st.bar_chart(df["status"].value_counts())
        with c2:
            st.markdown("#### Meetings by Type")
            st.bar_chart(df["meeting_type"].value_counts())

        df["meeting_date"] = pd.to_datetime(df["meeting_date"])
        monthly = df.groupby(df["meeting_date"].dt.to_period("M")).size().rename("meetings")
        st.markdown("#### Meetings Over Time")
        st.line_chart(monthly)

        if actions:
            adf = pd.DataFrame(actions)
            st.markdown("#### Action Item Completion")
            st.bar_chart(adf["status"].value_counts())
            completion = (adf["status"] == "Completed").mean() * 100
            st.metric("Action Completion Rate", f"{completion:.1f}%")
        else:
            st.info("No action items yet.")

# ---------- Export ----------
else:
    st.subheader("Export & Backup")
    st.write("Download your meeting and action-item data as JSON or CSV.")
    data = export_data()

    json_bytes = json.dumps(data, indent=2, default=str).encode("utf-8")
    st.download_button("⬇️ Download JSON Backup", json_bytes, "meeting_dashboard_backup.json", "application/json")

    meetings = pd.DataFrame(data["meetings"])
    actions = pd.DataFrame(data["action_items"])

    if not meetings.empty:
        st.download_button("⬇️ Meetings CSV", meetings.to_csv(index=False).encode(), "meetings.csv", "text/csv")
    if not actions.empty:
        st.download_button("⬇️ Action Items CSV", actions.to_csv(index=False).encode(), "action_items.csv", "text/csv")

    st.divider()
    st.markdown("### Data Overview")
    st.write(f"Meetings: **{len(data['meetings'])}**")
    st.write(f"Action items: **{len(data['action_items'])}**")
