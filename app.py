"""
Atlas: an airmail-themed front end for your LangGraph travel agent.

Run:   streamlit run app.py
Needs: your graph file saved as travel_agent.py (change GRAPH_MODULE below)
       exposing `app`, `llm` and `conn`, exactly as in your code.
"""
import ast
import hashlib
import importlib
import inspect
import json
import re
import time
import uuid
from datetime import date
from html import escape as esc

import pandas as pd
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

GRAPH_MODULE = "backend"

st.set_page_config(page_title="Atlas | Travel desk", page_icon="✈️", layout="wide")

_mod = importlib.import_module(GRAPH_MODULE)
graph_app, llm, conn = _mod.app, _mod.llm, _mod.conn

# `width="stretch"` on new Streamlit, `use_container_width` on older ones
STRETCH = (
    {"width": "stretch"}
    if "width" in inspect.signature(st.button).parameters
    else {"use_container_width": True}
)

STAGES = [
    ("flight_agent", "Flights", "Searching fares and routes"),
    ("hotel_agent", "Stays", "Scouting hotels on the web"),
    ("itinerary_agent", "Itinerary", "Drafting the day-by-day plan"),
    ("final_agent", "Trip brief", "Writing your final brief"),
]

EXAMPLES = {
    "Kyoto in April": "5 days in Kyoto from Delhi in April. Temples, tea houses and street food.",
    "Goa weekend": "Long weekend in Goa from Delhi, beach shacks and sunsets, under 25000 rupees.",
    "Vietnam, north to south": "10 days in Vietnam from Delhi, Hanoi to Ho Chi Minh City, street food and one trek.",
    "Santorini honeymoon": "Honeymoon in Santorini, 6 nights, flying from Mumbai, quiet and scenic.",
}

PLANE = '<svg width="14" height="14" viewBox="0 0 24 24"><path d="M2 12L22 3l-5 9 5 9z" fill="#fff"/></svg>'

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,800&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&display=swap');
:root{--paper:#E9EEF2;--card:#FFFFFF;--ink:#14213D;--red:#D7263D;--blue:#1F5FBF;--green:#2E7D5B;--grey:#5B6B7F;--line:#C5D0DB;}
.stApp{background:var(--paper);color:var(--ink);}
.stApp,.stMarkdown,label,textarea,input,button{font-family:'Bricolage Grotesque',sans-serif;}
.block-container{max-width:1120px;padding-top:2.2rem;}
header[data-testid="stHeader"]{background:transparent;}
[data-testid="stToolbar"],footer{display:none;}
section[data-testid="stSidebar"]{background:#DCE4EB;border-right:1px solid var(--line);}
.band{height:12px;border-radius:3px;margin:0 0 30px;background:repeating-linear-gradient(135deg,#D7263D 0 18px,#fff 18px 36px,#1F5FBF 36px 54px,#fff 54px 72px);}
.hero h1{font-weight:800;font-size:clamp(2.4rem,5.2vw,4.2rem);line-height:1;letter-spacing:-.035em;margin:0 0 .7rem;color:var(--ink);}
.hero p{font-family:'Newsreader',serif;font-size:1.25rem;line-height:1.55;max-width:58ch;color:var(--grey);margin:0 0 1.6rem;}
.brand{font-weight:800;font-size:1.9rem;letter-spacing:-.03em;line-height:1;color:var(--ink);}
.brand span{display:block;font-weight:400;font-size:.95rem;letter-spacing:0;color:var(--grey);margin-top:4px;}
.sec{font-weight:800;font-size:1.25rem;letter-spacing:-.02em;margin:26px 0 8px;}
.stTextArea textarea{background:#fff!important;border:1px solid var(--line)!important;border-radius:8px!important;font-family:'Newsreader',serif!important;font-size:1.2rem!important;line-height:1.5!important;color:var(--ink)!important;}
div[data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--line)!important;border-radius:12px!important;}
div[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown p,div[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown li{font-family:'Newsreader',serif;font-size:1.1rem;line-height:1.7;}
div[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown h1,div[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown h2,div[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown h3{font-family:'Bricolage Grotesque',sans-serif;letter-spacing:-.02em;}
button[data-testid="stBaseButton-primary"],div.stButton>button[kind="primary"]{background:var(--red);color:#fff;border:0;border-radius:8px;font-weight:800;font-size:1.05rem;padding:.7rem 1rem;}
button[data-testid="stBaseButton-primary"]:hover{background:#B81E32;color:#fff;}
button[data-testid="stBaseButton-secondary"],div.stButton>button[kind="secondary"]{background:#fff;border:1px solid var(--line);color:var(--ink);border-radius:4px;font-weight:600;}
button[data-testid="stBaseButton-secondary"]:hover{border-color:var(--blue);color:var(--blue);}
.stTabs [data-baseweb="tab"]{font-weight:600;font-size:1rem;}
.stTabs [aria-selected="true"]{color:var(--red);}
.stTabs [data-baseweb="tab-highlight"]{background:var(--red);}
.route{display:grid;grid-template-columns:repeat(4,1fr);background:var(--card);border:1px solid var(--line);border-radius:12px;padding:22px 10px 18px;margin:14px 0 18px;}
.leg{position:relative;padding:38px 8px 0;text-align:center;}
.leg:before{content:"";position:absolute;top:11px;left:50%;width:100%;height:3px;background:linear-gradient(90deg,var(--line) 50%,transparent 50%);background-size:14px 3px;}
.leg:last-child:before{display:none;}
.leg:after{content:"";position:absolute;top:2px;left:calc(50% - 10px);width:20px;height:20px;box-sizing:border-box;border-radius:50%;background:var(--card);border:3px solid var(--line);}
.leg.done:before{background:var(--blue);}
.leg.done:after{background:var(--blue);border-color:var(--blue);}
.leg.run:before{background:linear-gradient(90deg,var(--red) 50%,transparent 50%);background-size:14px 3px;animation:march .6s linear infinite;}
.leg.run:after{border-color:var(--red);}
@keyframes march{to{background-position:14px 0;}}
.plane{position:absolute;z-index:2;top:-2px;left:calc(50% - 14px);width:28px;height:28px;border-radius:50%;background:var(--red);display:grid;place-items:center;animation:pulse 1.4s ease-out infinite;}
.plane.landed{background:var(--green);animation:none;box-shadow:0 0 0 5px rgba(46,125,91,.18);}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(215,38,61,.45);}100%{box-shadow:0 0 0 12px rgba(215,38,61,0);}}
.leg .nm{font-weight:800;font-size:1.15rem;letter-spacing:-.02em;}
.leg .ds{color:var(--grey);font-size:.88rem;margin:2px 0 6px;}
.leg .st{font-size:.88rem;font-weight:600;color:var(--grey);}
.leg.run .st{color:var(--red);}
.leg.done .st{color:var(--green);}
.log{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--red);border-radius:4px 10px 10px 4px;padding:12px 18px;font-size:.92rem;line-height:1.75;font-variant-numeric:tabular-nums;}
.log b{color:var(--blue);display:inline-block;min-width:4.5em;}
.frame{padding:9px;border-radius:14px;margin:10px 0 14px;background:repeating-linear-gradient(135deg,#D7263D 0 16px,#fff 16px 32px,#1F5FBF 32px 48px,#fff 48px 64px);}
.ticket{display:flex;background:#fff;border-radius:7px;color:var(--ink);}
.ticket .main{flex:1;padding:24px 28px;min-width:0;}
.ticket .stub{width:210px;flex:none;border-left:2px dashed var(--line);padding:18px 14px;display:flex;flex-direction:column;align-items:center;justify-content:space-between;gap:8px;text-align:center;}
.ticket .for{color:var(--grey);font-size:.95rem;}
.ticket .dest{font-weight:800;font-size:clamp(1.4rem,2.8vw,2.2rem);line-height:1.1;letter-spacing:-.025em;margin:4px 0 20px;}
.ticket .fields{display:flex;flex-wrap:wrap;gap:12px 34px;}
.ticket .f small{display:block;color:var(--grey);font-size:.8rem;}
.ticket .f b{font-size:1.15rem;}
.stub small{color:var(--grey);font-size:.8rem;}
.stub .seat{font-weight:800;font-size:2.5rem;line-height:1;letter-spacing:-.03em;}
.summary{font-family:'Newsreader',serif;font-style:italic;font-size:1.1rem;color:var(--grey);margin:0 0 16px;}
.day-head{display:flex;align-items:center;gap:16px;margin:30px 0 10px;}
.stamp{border:2px dashed var(--blue);color:var(--blue);background:#fff;padding:4px 12px;border-radius:3px;transform:rotate(-2deg);font-weight:800;font-size:1.05rem;white-space:nowrap;}
.day-name{font-weight:800;font-size:1.65rem;letter-spacing:-.025em;line-height:1.1;}
.day-head:after{content:"";flex:1;border-top:1px dashed var(--line);}
.hcard{background:#fff;border:1px solid var(--line);border-left:4px solid var(--blue);border-radius:4px 10px 10px 4px;padding:14px 18px;margin-bottom:10px;}
.hcard a{color:var(--blue);font-weight:800;font-size:1.05rem;text-decoration:none;}
.hcard a:hover{text-decoration:underline;}
.hcard .dom{color:var(--grey);font-size:.82rem;margin-left:8px;}
.hcard p{font-family:'Newsreader',serif;font-size:1.02rem;line-height:1.55;color:#33415c;margin:.4rem 0 0;}
@media(max-width:800px){.route{grid-template-columns:1fr 1fr;row-gap:18px;}.leg:before{display:none;}.ticket{flex-direction:column;}.ticket .stub{width:auto;border-left:0;border-top:2px dashed var(--line);}}
@media(prefers-reduced-motion:reduce){.plane,.leg.run:before{animation:none;}}
"""


def html_block(s: str):
    """Render raw HTML; blank lines / indentation would break Markdown's HTML block."""
    st.markdown("\n".join(l.strip() for l in s.splitlines() if l.strip()), unsafe_allow_html=True)


html_block(f"<style>{CSS}</style>")


# ───────────────────────── helpers ─────────────────────────
def text_of(c) -> str:
    """Gemini can return a list of content blocks; always flatten to text."""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "".join(p if isinstance(p, str) else p.get("text", "") for p in c if isinstance(p, (str, dict)))
    return str(c or "")


def kb(n: int) -> str:
    return f"{n / 1024:.1f} KB"


def cfg(tid: str) -> dict:
    return {"configurable": {"thread_id": tid}}


def pipeline_html(state: dict, times: dict) -> str:
    cur = next((i for i, (k, _, _) in enumerate(STAGES) if state[k] == "run"), None)
    all_done = all(state[k] == "done" for k, _, _ in STAGES)
    legs = []
    for i, (k, name, desc) in enumerate(STAGES):
        s = state[k]
        plane = ""
        if cur == i:
            plane = f'<span class="plane">{PLANE}</span>'
        elif all_done and i == len(STAGES) - 1:
            plane = f'<span class="plane landed">{PLANE}</span>'
        if s == "done":
            status = f"Done in {times[k]:.1f} s" if k in times else "Done"
        else:
            status = "Working" if s == "run" else "Waiting"
        legs.append(
            f'<div class="leg {s}">{plane}<div class="nm">{name}</div>'
            f'<div class="ds">{desc}</div><div class="st">{status}</div></div>'
        )
    return '<div class="route">' + "".join(legs) + "</div>"


def compose_query(base: str, meta: dict, enrich: bool) -> str:
    base = base.strip()
    if not enrich:
        return base
    bits = [f"{meta['days']} days", f"{meta['travelers']} traveler(s)", f"{meta['budget']} budget"]
    if meta["vibes"]:
        bits.append("interests: " + ", ".join(meta["vibes"]))
    return f"{base} ({'; '.join(bits)})"


def run_trip(query: str, meta: dict, pipe_slot, log_slot) -> dict:
    tid = f"trip_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    order = [k for k, _, _ in STAGES]
    state = {k: "wait" for k in order}
    state[order[0]] = "run"
    times, log, vals = {}, [], {"calls": 0}
    start = last = time.time()
    pipe_slot.markdown(pipeline_html(state, times), unsafe_allow_html=True)

    payload = {
        "messages": [HumanMessage(content=query)],
        "user_query": query,
        "flight_results": "",
        "hotel_results": "",
        "itinerary": "",
        "llm_calls": 0,
    }
    for chunk in graph_app.stream(payload, config=cfg(tid), stream_mode="updates"):
        for node, upd in chunk.items():
            now = time.time()
            times[node], last = now - last, now
            state[node] = "done"
            if node in order and order.index(node) + 1 < len(order):
                state[order[order.index(node) + 1]] = "run"

            if node == "flight_agent":
                vals["flight"] = upd.get("flight_results", "")
                note = f"Flights: {kb(len(str(vals['flight'])))} of fare data"
            elif node == "hotel_agent":
                vals["hotel"] = upd.get("hotel_results", "")
                note = f"Stays: {kb(len(str(vals['hotel'])))} of hotel results"
            elif node == "itinerary_agent":
                vals["itinerary"] = text_of(upd.get("itinerary", ""))
                note = f"Itinerary: {len(vals['itinerary'].split())} words drafted"
            else:
                msgs = upd.get("messages") or []
                vals["final"] = text_of(msgs[-1].content) if msgs else ""
                note = f"Trip brief: {len(vals['final'].split())} words written"
            vals["calls"] = max(vals["calls"], upd.get("llm_calls", 0) or 0)
            log.append(f"<b>{now - start:.1f} s</b>{esc(note)}")

            pipe_slot.markdown(pipeline_html(state, times), unsafe_allow_html=True)
            log_slot.markdown(f'<div class="log">{"<br>".join(log)}</div>', unsafe_allow_html=True)

    return {
        "thread_id": tid,
        "query": query,
        "flight": vals.get("flight", ""),
        "hotel": vals.get("hotel", ""),
        "itinerary": vals.get("itinerary", ""),
        "final": vals.get("final", ""),
        "calls": vals["calls"],
        "elapsed": time.time() - start,
        "times": times,
        "log": log,
        "meta": meta,
    }


def load_trip(tid: str) -> dict:
    v = graph_app.get_state(cfg(tid)).values or {}
    msgs = v.get("messages", [])
    return {
        "thread_id": tid,
        "query": v.get("user_query", ""),
        "flight": v.get("flight_results", ""),
        "hotel": v.get("hotel_results", ""),
        "itinerary": text_of(v.get("itinerary", "")),
        "final": text_of(msgs[-1].content) if msgs else "",
        "calls": v.get("llm_calls", 0),
        "elapsed": None,
        "times": {},
        "log": [],
        "meta": {},
    }


def list_threads(limit: int = 10):
    try:
        rows = conn.execute(
            "SELECT thread_id, MAX(checkpoint_id) m FROM checkpoints "
            "GROUP BY thread_id ORDER BY m DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []


@st.cache_data(ttl=120, show_spinner=False)
def vault_label(tid: str) -> str:
    try:
        q = (graph_app.get_state(cfg(tid)).values or {}).get("user_query") or tid
    except Exception:
        q = tid
    return q if len(q) <= 44 else q[:44] + "…"


def parse_blob(b):
    if isinstance(b, (dict, list)):
        return b
    s = str(b).strip()
    for loader in (json.loads, ast.literal_eval):
        try:
            return loader(s)
        except Exception:
            pass
    return s


def extract_rows(data):
    if isinstance(data, list) and data and all(isinstance(x, dict) for x in data):
        return data
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                return v
    return None


def show_table(rows):
    df = pd.json_normalize(rows).astype(object)
    df = df.apply(
        lambda col: col.map(
            lambda x: x if isinstance(x, (str, int, float, bool, type(None))) else json.dumps(x, default=str)
        )
    )
    st.dataframe(df, hide_index=True, **STRETCH)


def render_flights(blob):
    data = parse_blob(blob)
    rows = extract_rows(data)
    if rows:
        show_table(rows)
    elif isinstance(data, (dict, list)):
        st.json(data)
    else:
        with st.container(border=True):
            st.markdown(str(data) or "No flight data came back.")


def render_hotels(blob):
    data = parse_blob(blob)
    rows = extract_rows(data)
    if rows and any("url" in r for r in rows):
        for r in rows:
            url = str(r.get("url", ""))
            title = esc(str(r.get("title") or url or "Result"))
            dom = esc(re.sub(r"^https?://(www\.)?", "", url).split("/")[0])
            body = esc(str(r.get("content", ""))[:340])
            link = f'<a href="{esc(url)}" target="_blank">{title}</a>' if url.startswith("http") else title
            html_block(f'<div class="hcard">{link}<span class="dom">{dom}</span><p>{body}</p></div>')
    else:
        render_flights(blob)


def split_days(text: str):
    parts = re.split(r"(?im)^[ \t]*(?:#{1,6}[ \t]*)?(?:\*\*)?[ \t]*(day[ \t]*\d+\b[^\n]*)$", text)
    days = []
    for i in range(1, len(parts) - 1, 2):
        title = parts[i].strip(" *#:\t")
        m = re.match(r"(?i)day\s*(\d+)\s*[:\-–—|]*\s*(.*)", title)
        num, name = (int(m.group(1)), m.group(2).strip(" *#:")) if m else (len(days) + 1, title)
        days.append((num, name, parts[i + 1]))
    return parts[0], days


def ticket_html(trip: dict, passenger: str) -> str:
    seed = hashlib.md5(trip["thread_id"].encode()).hexdigest()
    gate = "ABCDEFGH"[int(seed[0], 16) % 8] + str(int(seed[1:3], 16) % 30 + 1)
    seat = f"{int(seed[3:5], 16) % 32 + 1}{'ABCDEF'[int(seed[5], 16) % 6]}"
    m = trip.get("meta") or {}
    q = trip["query"]
    q = q if len(q) <= 110 else q[:110] + "…"
    today = date.today()
    fields = [
        ("Travelers", m.get("travelers", "-")),
        ("Length", f"{m['days']} days" if m.get("days") else "-"),
        ("Budget", m.get("budget", "-")),
        ("Gate", gate),
    ]
    fhtml = "".join(f'<div class="f"><small>{k}</small><b>{esc(str(v))}</b></div>' for k, v in fields)
    postmark = (
        '<svg width="130" height="62" viewBox="0 0 130 62">'
        '<circle cx="31" cy="31" r="27" fill="none" stroke="#1F5FBF" stroke-width="2"/>'
        '<circle cx="31" cy="31" r="21" fill="none" stroke="#1F5FBF" stroke-width="1" stroke-dasharray="2 3"/>'
        f'<text x="31" y="30" text-anchor="middle" font-size="10" font-weight="700" fill="#1F5FBF">{today.strftime("%d %b")}</text>'
        f'<text x="31" y="43" text-anchor="middle" font-size="9" fill="#1F5FBF">{today.year}</text>'
        '<path d="M62 20q8-6 16 0t16 0t16 0M62 31q8-6 16 0t16 0t16 0M62 42q8-6 16 0t16 0t16 0" '
        'fill="none" stroke="#1F5FBF" stroke-width="2" stroke-linecap="round"/></svg>'
    )
    return (
        f'<div class="frame"><div class="ticket"><div class="main">'
        f'<div class="for">Prepared for {esc(passenger)}</div>'
        f'<div class="dest">{esc(q)}</div><div class="fields">{fhtml}</div></div>'
        f'<div class="stub"><div><small>Seat</small><div class="seat">{seat}</div></div>{postmark}</div>'
        f"</div></div>"
    )


def dossier_md(t: dict) -> str:
    return (
        f"# Trip brief\n\n> {t['query']}\n\n{t['final']}\n\n---\n\n## Itinerary\n\n{t['itinerary']}\n\n"
        f"## Flights\n\n```\n{t['flight']}\n```\n\n## Stays\n\n```\n{t['hotel']}\n```\n"
    )


def concierge_stream(t: dict, history: list, question: str):
    ctx = (
        "You are the concierge of a travel desk. Answer follow-up questions about this specific trip. "
        "Stay consistent with the data below, say so when something is not covered, and keep answers practical.\n\n"
        f"Request: {t['query']}\n\nFlights:\n{str(t['flight'])[:6000]}\n\nHotels:\n{str(t['hotel'])[:6000]}\n\n"
        f"Itinerary:\n{t['itinerary'][:8000]}\n\nBrief:\n{t['final'][:6000]}"
    )
    msgs = [SystemMessage(content=ctx)]
    for role, txt in history:
        msgs.append(HumanMessage(content=txt) if role == "user" else AIMessage(content=txt))
    msgs.append(HumanMessage(content=question))
    for ch in llm.stream(msgs):
        piece = text_of(ch.content)
        if piece:
            yield piece


def set_query(q: str):
    st.session_state.query_text = q


def open_trip(tid: str):
    t = load_trip(tid)
    st.session_state.trip = t
    st.session_state.query_text = t["query"]


def clear_trip():
    st.session_state.trip = None
    st.session_state.query_text = ""


def ask_chip(q: str):
    st.session_state.pending_q = q


# ───────────────────────── state + sidebar ─────────────────────────
st.session_state.setdefault("trip", None)
st.session_state.setdefault("chats", {})
st.session_state.setdefault("query_text", "")
st.session_state.setdefault("passenger", "Traveler")

with st.sidebar:
    html_block('<div class="brand">Atlas<span>Your four-agent travel desk</span></div>')
    st.text_input("Passenger name", key="passenger")

passenger = st.session_state.passenger.strip() or "Traveler"

# ───────────────────────── hero + planner ─────────────────────────
html_block(
    f"""
    <div class="band"></div>
    <div class="hero">
    <h1>Where are you flying, {esc(passenger)}?</h1>
    <p>Describe the trip in your own words. One agent compares flights, another scouts hotels,
    a third drafts the itinerary and the last one writes you a brief you can act on.</p>
    </div>
    """
)

with st.container(border=True):
    st.text_area(
        "Describe your trip",
        key="query_text",
        height=110,
        placeholder="Example: 6 days in Lisbon from Delhi in May, old neighbourhoods, seafood, one day trip to Sintra",
        label_visibility="collapsed",
    )
    chip_cols = st.columns(len(EXAMPLES))
    for i, (label, q) in enumerate(EXAMPLES.items()):
        chip_cols[i].button(label, key=f"ex_{i}", on_click=set_query, args=(q,), **STRETCH)

    c1, c2, c3, c4 = st.columns([1, 1.4, 1.2, 2])
    travelers = c1.number_input("Travelers", 1, 12, 2)
    days = c2.slider("Trip length (days)", 2, 21, 5)
    budget = c3.selectbox("Budget", ["Lean", "Comfortable", "Premium", "No limit"], index=1)
    vibes = c4.multiselect(
        "What matters most",
        ["Food", "Culture", "Nature", "Nightlife", "Adventure", "Relaxation", "Shopping", "Photography"],
    )
    enrich = st.checkbox("Add these details to what the agents receive", value=True)
    go = st.button("Plan my trip", type="primary", **STRETCH)

pipe_slot = st.empty()
log_slot = st.empty()

# ───────────────────────── run ─────────────────────────
if go:
    base = st.session_state.query_text.strip()
    if not base:
        st.warning("Describe the trip first, then press Plan my trip.")
    else:
        meta = {"travelers": travelers, "days": days, "budget": budget, "vibes": vibes}
        try:
            st.session_state.trip = run_trip(compose_query(base, meta, enrich), meta, pipe_slot, log_slot)
            log_slot.empty()
        except Exception as e:
            pipe_slot.empty()
            st.error(f"The run stopped before it finished: {e}")
            with st.expander("Error details"):
                st.exception(e)
elif st.session_state.trip:
    t0 = st.session_state.trip
    pipe_slot.markdown(
        pipeline_html({k: "done" for k, _, _ in STAGES}, t0.get("times", {})), unsafe_allow_html=True
    )

# ───────────────────────── results ─────────────────────────
trip = st.session_state.trip
if trip:
    html_block(ticket_html(trip, passenger))

    kb_data = len(str(trip["flight"])) + len(str(trip["hotel"]))
    if trip["elapsed"] is not None:
        line = f"Landed in {trip['elapsed']:.1f} s using {trip['calls']} model calls and {kb(kb_data)} of live search data."
    else:
        line = f"Restored from your vault: {trip['calls']} model calls and {kb(kb_data)} of search data."
    html_block(f'<p class="summary">{line}</p>')

    tab_brief, tab_days, tab_flights, tab_stays, tab_run = st.tabs(
        ["Trip brief", "Day by day", "Flights", "Stays", "Run details"]
    )

    with tab_brief:
        with st.container(border=True):
            st.markdown(trip["final"] or "No brief was generated for this trip.")
        d1, d2, _ = st.columns([1, 1, 2])
        d1.download_button(
            "Download brief (.md)", dossier_md(trip), file_name="trip-brief.md", mime="text/markdown", **STRETCH
        )
        d2.download_button(
            "Download raw data (.json)",
            json.dumps(trip, indent=2, default=str),
            file_name="trip-data.json",
            mime="application/json",
            **STRETCH,
        )

    with tab_days:
        intro, day_list = split_days(trip["itinerary"])
        if len(day_list) >= 2:
            if intro.strip():
                st.markdown(intro.strip())
            for num, name, body in day_list:
                html_block(
                    f'<div class="day-head"><span class="stamp">Day {num}</span>'
                    f'<span class="day-name">{esc(name or "Open day")}</span></div>'
                )
                with st.container(border=True):
                    st.markdown(body.strip() or "Nothing planned yet.")
        else:
            with st.container(border=True):
                st.markdown(trip["itinerary"] or "No itinerary was generated.")

    with tab_flights:
        render_flights(trip["flight"])

    with tab_stays:
        render_hotels(trip["hotel"])

    with tab_run:
        if trip["log"]:
            html_block(f'<div class="log">{"<br>".join(trip["log"])}</div>')
        else:
            st.caption("Timing is only recorded for trips planned in this session.")
        st.caption(f"Checkpoint thread: {trip['thread_id']}")
        with st.expander("What the agents received"):
            st.code(trip["query"], language=None)

    # ── concierge ──
    html_block('<div class="sec">Ask the concierge about this trip</div>')
    tid = trip["thread_id"]
    history = st.session_state.chats.setdefault(tid, [])

    chip_q = ["Make it cheaper", "Add a rainy-day plan", "Build a packing list", "Swap in more food stops"]
    cc = st.columns(len(chip_q))
    for i, q in enumerate(chip_q):
        cc[i].button(q, key=f"cc_{i}", on_click=ask_chip, args=(q,), **STRETCH)

    for role, txt in history:
        with st.chat_message(role):
            st.markdown(txt)

    question = st.chat_input("Ask a follow-up about this trip") or st.session_state.pop("pending_q", None)
    if question:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            try:
                answer = st.write_stream(concierge_stream(trip, history, question))
                history.append(("user", question))
                history.append(("assistant", answer))
            except Exception as e:
                st.error(f"The concierge could not answer: {e}")

# ───────────────────────── vault (end of script so new trips show up at once) ─────────────────────────
with st.sidebar:
    html_block('<div class="sec">Trip vault</div>')
    threads = list_threads()
    if not threads:
        st.caption("Trips you plan are saved here and can be reopened any time.")
    for i, tid_ in enumerate(threads):
        st.button(vault_label(tid_), key=f"vault_{i}", on_click=open_trip, args=(tid_,), **STRETCH)
    if st.session_state.trip:
        st.button("Start a new trip", on_click=clear_trip, **STRETCH)