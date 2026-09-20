import sys
import os
import time
import re
import subprocess
import glob
import json
import streamlit as st

# Sync Streamlit Cloud secrets to os.environ so pipeline subprocesses can access GROQ_API_KEY
if hasattr(st, "secrets"):
    try:
        for _k, _v in st.secrets.items():
            if isinstance(_v, (str, int, float, bool)) and _k not in os.environ:
                os.environ[_k] = str(_v)
    except Exception:
        pass

st.set_page_config(page_title="AI Dev Team", page_icon="🤖", layout="wide")

if "last_run_stats" not in st.session_state:
    st.session_state.last_run_stats = None


# VS Code Dark+ Theme CSS + Sidebar Styles
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { 
        background: radial-gradient(circle at 50% 0%, #151b28 0%, #0d1117 60%) !important; 
        color: #c9d1d9; 
        border: 18px solid #586069 !important; /* 4.5x thickness border around entire app */
        box-sizing: border-box !important;
    }
    [data-testid="stSidebar"] { 
        background-color: #010409 !important; 
        border-right: 12px solid #586069 !important; /* Tripled grey separating border */
        box-shadow: 2px 0 20px rgba(88, 96, 105, 0.15);
    }
    [data-testid="stSidebar"] * { color: #c9d1d9; }
    
    /* Sidebar History items hover effect */
    /* Switch User and New Chat Buttons (Cream color) */
    [data-testid="stSidebar"] div[data-testid="stButton"] > button {
        background: #fff8dc !important; /* Cream color */
        color: #000000 !important;
        border: 4px solid #fff8dc !important; 
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important; /* Proper damping */
        border-radius: 6px !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button * {
        color: #000000 !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    
    /* Task History Buttons (White filled) */
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] > div:nth-child(1) button {
        background: #ffffff !important;
        color: #000000 !important;
        border: 4px solid #ffffff !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] > div:nth-child(1) button * {
        color: #000000 !important;
        font-weight: 700 !important;
        transition: color 0.3s ease !important;
    }
    
    /* Delete Buttons (Black filled, purple symbol, white border) */
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
        background: #000000 !important;
        color: #bd58ff !important;
        border: 4px solid #ffffff !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] > div:nth-child(2) button * {
        color: #bd58ff !important;
        font-weight: 900 !important;
        transition: color 0.3s ease !important;
    }

    /* Proper Hover state for Top buttons */
    [data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
        border-color: #00eeff !important;
        box-shadow: 0 0 10px #00eeff, 0 4px 15px rgba(0,238,255,0.4) !important;
        background-color: #010409 !important;
        transform: translateX(4px) !important;
    }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button:hover * {
        color: #00eeff !important;
    }

    /* Bulletproof Hover state for History and Delete buttons */
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] > div:nth-child(1) button:hover,
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] > div:nth-child(2) button:hover {
        border-color: #00eeff !important;
        box-shadow: 0 0 10px #00eeff, 0 4px 15px rgba(0,238,255,0.4) !important;
        background-color: #010409 !important;
        transform: translateX(4px) !important;
    }
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] > div:nth-child(1) button:hover *,
    [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] > div:nth-child(2) button:hover * {
        color: #00eeff !important;
    }
    
    .history-title {
        border: 4px solid #ff0055;
        background: rgba(255, 0, 85, 0.1);
        color: #ffffff;
        padding: 12px;
        border-radius: 8px;
        font-size: 1.5rem;
        font-weight: 900;
        text-align: center;
        text-transform: uppercase;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(255, 0, 85, 0.2);
    }
    
    .username-label {
        border: 4px solid #ff8800;
        background: rgba(255, 136, 0, 0.1);
        padding: 12px;
        border-radius: 8px;
        text-transform: uppercase;
        text-align: center;
        color: #ffffff !important;
        font-weight: 700;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(255, 136, 0, 0.2);
    }
    
    .sidebar-new-btn > button { 
        background: linear-gradient(180deg, #2ea043 0%, #238636 100%) !important; 
        border: 1px solid rgba(240,246,252,0.1) !important; 
        border-radius: 8px !important; margin-bottom: 20px; font-weight: 600 !important; color: white !important;
        transition: all 0.3s ease !important;
    }
    .sidebar-new-btn > button:hover { 
        background: #2ea043 !important;
        box-shadow: 0 4px 15px rgba(46, 160, 67, 0.4) !important; 
        transform: translateY(-1px);
    }
    
    .main-title { 
        font-size: 3rem; font-weight: 800; 
        background: linear-gradient(90deg, #58a6ff, #bd58ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px; letter-spacing: -1px; 
        text-shadow: 0px 4px 20px rgba(88, 166, 255, 0.2);
    }
    .sub-title { 
        font-size: 1.1rem; 
        background: linear-gradient(90deg, #58a6ff, #bd58ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 30px; font-weight: 700; 
        letter-spacing: 1px; text-transform: uppercase;
        text-shadow: 0px 4px 20px rgba(189, 88, 255, 0.3);
    }
    .header-box {
        border: 4px solid #ffcc00;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        background: rgba(255, 204, 0, 0.05);
        margin-bottom: 25px;
        box-shadow: 0 0 20px rgba(255, 204, 0, 0.3);
    }

    /* Expander Box (Improvement Statistics) */
    [data-testid="stExpander"] {
        border: 4px solid #0066ff !important; /* Vibrant Blue Border */
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(0, 102, 255, 0.25) !important;
        background: rgba(13, 17, 23, 0.6) !important;
        margin-bottom: 20px;
    }

    /* Text areas and Input fields (Blended green-blue shade) */
    .stTextArea textarea, .stTextInput input {
        background-color: rgba(13, 17, 23, 0.7) !important; 
        border: 4px solid #00f2c3 !important; /* Blended green-blue / teal */
        border-radius: 8px !important; color: #c9d1d9 !important; padding: 14px !important; 
        box-shadow: 0 4px 15px rgba(0, 242, 195, 0.15) !important; transition: all 0.3s ease;
    }
    .stTextArea textarea:focus, .stTextInput input:focus { 
        border-color: #00eeff !important; 
        box-shadow: 0 0 20px rgba(0, 238, 255, 0.4) !important; 
        background-color: #0d1117 !important;
    }
    label, .stMarkdown p { color: #8b949e !important; font-size: 0.95rem !important; font-weight: 500 !important; }
    
    /* Main Action Button */
    [data-testid="baseButton-primary"] {
        background: #ffcc00 !important; /* Filled dark yellow vibrant */
        color: #000000 !important;
        border: 4px solid #ffcc00 !important;
        border-radius: 8px !important; font-weight: 900 !important;
        font-size: 1.2rem !important;
        padding: 14px 20px !important; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        box-shadow: 0 4px 15px rgba(255, 204, 0, 0.4) !important;
    }
    [data-testid="baseButton-primary"] * {
        color: #000000 !important;
        font-weight: 900 !important;
    }
    [data-testid="baseButton-primary"]:hover { 
        box-shadow: 0 6px 25px rgba(255, 204, 0, 0.6) !important; 
        transform: translateY(-2px) !important;
        filter: brightness(1.1) !important;
    }
    
    /* Approve Button (Kept untouched) */
    .approve-btn > div[data-testid="stButton"] > button {
        background: linear-gradient(180deg, #2ea043 0%, #238636 100%) !important; 
        border: 1px solid rgba(240,246,252,0.1) !important;
        color: #ffffff !important; font-weight: 600 !important; border-radius: 6px !important;
    }
    .approve-btn > div[data-testid="stButton"] > button:hover { background: #2ea043 !important; }
    
    /* Reject Button (Kept untouched) */
    .reject-btn > div[data-testid="stButton"] > button {
        background: linear-gradient(180deg, #da3633 0%, #b31d28 100%) !important; 
        border: 1px solid rgba(240,246,252,0.1) !important;
        color: #ffffff !important; font-weight: 600 !important; border-radius: 6px !important;
    }
    .reject-btn > div[data-testid="stButton"] > button:hover { background: #da3633 !important; }

    /* Code Blocks and Glassmorphism */
    div[data-testid="stCodeBlock"] { 
        background-color: #161b22 !important; border: 1px solid #30363d !important; 
        border-radius: 10px !important; box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
    }
    div[data-testid="stCodeBlock"] code { color: #e6edf3 !important; font-family: 'Fira Code', Consolas, monospace !important; font-size: 0.9rem !important; }
    
    div[data-testid="stAlert"] {
        background: rgba(22, 27, 34, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(88, 166, 255, 0.3) !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15) !important;
    }

    .approval-card, .code-viewer-card, .username-bar {
        background: rgba(22, 27, 34, 0.5); backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.05); border-radius: 12px;
        padding: 24px; margin-top: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    .approval-card:hover, .code-viewer-card:hover, .username-bar:hover {
        border-color: rgba(88, 166, 255, 0.2);
        box-shadow: 0 8px 32px rgba(88, 166, 255, 0.08);
    }
    .approval-card { border-left: 4px solid #58a6ff; }
    .code-viewer-card { border-left: 4px solid #bd58ff; }
    
    .code-viewer-title {
        font-size: 1.2rem; font-weight: 700; color: #bd58ff; margin-bottom: 12px;
    }
    .username-label {
        color: #58a6ff !important; font-size: 0.85rem !important; font-weight: 700 !important;
        margin-bottom: 2px !important; text-transform: uppercase; letter-spacing: 1px;
    }

    /* Custom Login Card */
    .login-card {
        background: rgba(22, 27, 34, 0.6);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(88, 166, 255, 0.2);
        border-radius: 16px;
        padding: 40px;
        max-width: 450px;
        margin: 0 auto;
        box-shadow: 0 12px 40px rgba(0,0,0,0.3), 0 0 20px rgba(88, 166, 255, 0.1);
    }
    .login-btn-wrapper { margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

_DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_DASHBOARD_DIR)
_TASKS_BASE_DIR = os.path.join(_DASHBOARD_DIR, "tasks")


# ---------------------------------------------------------------------------
# Helper: per-user tasks directory
# ---------------------------------------------------------------------------
def _get_user_tasks_dir(username: str) -> str:
    """Return the tasks directory for a specific user."""
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', username.strip().lower())
    if not safe_name:
        safe_name = "default"
    return os.path.join(_TASKS_BASE_DIR, safe_name)


# ---------------------------------------------------------------------------
# Helper: extract generated Python code from unified diff
# ---------------------------------------------------------------------------
def _extract_generated_code(code_diff: str) -> dict:
    """
    Parse a unified diff string and extract the full generated source code
    for each file mentioned in the diff.
    
    Returns a dict mapping filename -> full source code string.
    """
    if not code_diff:
        return {}

    files = {}
    current_file = None
    current_lines = []

    for line in code_diff.split("\n"):
        # Detect file header: +++ b/filename.py
        if line.startswith("+++ "):
            # Save previous file if any
            if current_file and current_lines:
                files[current_file] = "\n".join(current_lines)
            # Extract filename from +++ b/filename or +++ b/path/to/file
            path = line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            current_file = path
            current_lines = []
            continue

        # Skip --- header lines and @@ hunk markers
        if line.startswith("--- ") or line.startswith("@@"):
            continue

        # Lines starting with '+' are added lines (the generated code)
        if line.startswith("+"):
            current_lines.append(line[1:])  # strip the leading '+'
        # Context lines (no prefix or space prefix) are also part of the code
        elif line.startswith(" "):
            current_lines.append(line[1:])  # strip the leading space
        # Lines starting with '-' are removed lines — skip them
        elif line.startswith("-"):
            continue
        # Blank lines in the diff that belong to code
        elif line == "":
            if current_file is not None:
                current_lines.append("")

    # Save last file
    if current_file and current_lines:
        files[current_file] = "\n".join(current_lines)

    # Strip trailing blank lines from each file
    for fname in files:
        files[fname] = files[fname].rstrip("\n") + "\n"

    return files


# ---------------------------------------------------------------------------
# Username management via query params + session state
# ---------------------------------------------------------------------------
if "username" not in st.session_state:
    # Try to restore from query params (survives page refresh)
    params = st.query_params
    if "user" in params:
        st.session_state.username = params["user"]
    else:
        st.session_state.username = ""

if "form_reset_counter" not in st.session_state:
    st.session_state.form_reset_counter = 0

# If no username yet, show a login prompt and stop
if not st.session_state.username:
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='header-box'><div class='main-title' style='text-align: center;'>🤖 AI DEV TEAM</div><div class='sub-title' style='text-align: center; margin-bottom: 0;'>A MULTI AGENT MODEL FOR DEALING WITH PYTHON PROJECTS</div></div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align: center; color: #e6edf3; margin-top: 0;'>👤 Access Workspace</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8b949e; margin-bottom: 20px;'>Your task history will be private to your username.</p>", unsafe_allow_html=True)
    
    # Adding columns to naturally center the input field in Streamlit
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        entered_name = st.text_input("Username", key="username_input", placeholder="e.g. rithwik, soumya, dev1", label_visibility="collapsed")
        
        st.markdown('<div class="primary-btn login-btn-wrapper">', unsafe_allow_html=True)
        if st.button("Enter Workspace →", use_container_width=True):
            if entered_name.strip():
                st.session_state.username = entered_name.strip()
                st.query_params["user"] = entered_name.strip()
                st.rerun()
            else:
                st.error("Please enter a username.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# At this point we have a valid username
current_username = st.session_state.username
# Ensure query param is in sync
st.query_params["user"] = current_username
_USER_TASKS_DIR = _get_user_tasks_dir(current_username)
os.makedirs(_USER_TASKS_DIR, exist_ok=True)


# --- SIDEBAR LOGIC ---
with st.sidebar:
    st.markdown("<div class='history-title'>History</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='username-label'>👤 Logged in as: {current_username}</div>", unsafe_allow_html=True)

    # Logout / switch user button
    if st.button("🔄 Switch User", use_container_width=True, key="switch_user"):
        st.session_state.username = ""
        st.session_state.selected_task_file = None
        if "user" in st.query_params:
            del st.query_params["user"]
        st.rerun()

    st.markdown('<div class="sidebar-new-btn">', unsafe_allow_html=True)
    if st.button("📝 New chat (Reset)", use_container_width=True):
        st.session_state.form_reset_counter += 1
        st.session_state.selected_task_file = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### Recents")
    task_files = glob.glob(os.path.join(_USER_TASKS_DIR, "*.json"))
    task_files.sort(key=os.path.getctime, reverse=True)
    
    if not task_files:
        st.caption("No history yet.")
    else:
        for f in task_files:
            try:
                with open(f, "r", encoding="utf-8") as f_in:
                    data = json.load(f_in)
                t_id = data.get("task_id", os.path.basename(f))
                t_req = data.get("feature_request", "No description")
                t_status = data.get("status", "")
                
                # Truncate description for sidebar
                if len(t_req) > 35:
                    t_req = t_req[:32] + "..."
                    
                # 2-column layout for the history item and the delete button
                scol1, scol2 = st.columns([3, 1])
                with scol1:
                    is_failed = False
                    if "run_stats" in data:
                        is_failed = (data["run_stats"].get("status") == "error")
                    else:
                        diff = data.get("code_diff")
                        is_failed = not diff or diff.count("+++ ") == 0

                    if t_status in ("approved", "verified_fixed"):
                        icon = "✅"
                    elif is_failed:
                        icon = "❌"
                    elif t_status == "awaiting_human_approval":
                        icon = "👀"
                    else:
                        icon = "📄"
                        
                    if st.button(f"{icon} {t_id}\n{t_req}", key=f"sel_{t_id}", use_container_width=True):
                        st.session_state.selected_task_file = f
                        st.rerun()
                with scol2:
                    if st.button("✖", key=f"del_{t_id}", help="Delete"):
                        os.remove(f)
                        if st.session_state.get("selected_task_file") == f:
                            st.session_state.selected_task_file = None
                        st.rerun()
            except json.JSONDecodeError:
                st.sidebar.warning(f"⚠️ Corrupted task file: {os.path.basename(f)}")
            except Exception as e:
                pass

# Load selected task data if present
loaded_req = ""
loaded_repo = "sample_repo/flaskbb"
loaded_tid = f"live_{int(time.time()) % 1000:03d}"
loaded_diff = None
loaded_plan = None
loaded_task_data = None

if st.session_state.get("selected_task_file") and os.path.exists(st.session_state.selected_task_file):
    try:
        with open(st.session_state.selected_task_file, "r", encoding="utf-8") as f_in:
            sel_data = json.load(f_in)
            loaded_task_data = sel_data
            loaded_req = sel_data.get("feature_request", "")
            loaded_tid = sel_data.get("task_id", "")
            loaded_diff = sel_data.get("code_diff")
            loaded_plan = sel_data.get("plan")
    except json.JSONDecodeError:
        st.error(f"⚠️ Error: The selected task file ({os.path.basename(st.session_state.selected_task_file)}) is corrupted.")
    except Exception:
        pass


import uuid as _uuid

# --- MAIN CONTENT ---
st.markdown("<div class='header-box'><div class='main-title'>🤖 AI DEV TEAM</div><div class='sub-title' style='margin-bottom: 0;'>A MULTI AGENT MODEL FOR DEALING WITH PYTHON PROJECTS</div></div>", unsafe_allow_html=True)

import streamlit.components.v1 as components

def get_svg_html(active_agent=None):
    # active_agent can be 'pm', 'architect', 'coding', 'review', 'testing', 'manager', 'reflection'
    
    html = """
<!DOCTYPE html>
<html>
<head>
<style>
  @keyframes beep {
      0% { stroke: #ffffff; stroke-width: 2px; filter: drop-shadow(0 0 2px rgba(255,255,255,0.8)); }
      100% { stroke: #00eeff; stroke-width: 6px; filter: drop-shadow(0 0 15px rgba(0,238,255,1)); }
  }
  .active-beep {
      animation: beep 0.6s infinite alternate !important;
      stroke-dasharray: none !important;
  }

  html, body { height: 100%; margin: 0; padding: 0; overflow: hidden; background: transparent; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
  
  .diagram-container {
      width: calc(100% - 20px);
      height: calc(100% - 20px);
      margin: 10px;
      overflow: auto; /* Makes it a scrollable entity */
      background: #0d1117;
      border: 4px solid #00eeff; /* Vibrant cyan border */
      border-radius: 12px;
      box-shadow: 0 0 25px rgba(0, 238, 255, 0.25), inset 0 0 20px rgba(0,0,0,0.5); /* Cyan vibe */
  }

  /* Custom scrollbar for the scrollable entity */
  .diagram-container::-webkit-scrollbar { width: 12px; height: 12px; }
  .diagram-container::-webkit-scrollbar-track { background: #0a0e17; border-radius: 8px; border: 1px solid #30363d; }
  .diagram-container::-webkit-scrollbar-thumb { background: #00eeff; border-radius: 8px; border: 2px solid #0a0e17; }
  .diagram-container::-webkit-scrollbar-thumb:hover { background: #00b3cc; }

  .box { stroke: rgba(255,255,255,0.15); stroke-width: 2; rx: 8; ry: 8; }
  .text { fill: #ffffff; font-size: 13px; font-weight: bold; text-anchor: middle; dominant-baseline: middle; }
  .line { stroke: #8b949e; stroke-width: 2; fill: none; marker-end: url(#arrow); }
  .leg-text { fill: #c9d1d9; font-size: 13px; }
  .circ { fill: #161b22; stroke: #8b949e; stroke-width: 1; }
  .circ-text { fill: #c9d1d9; font-size: 10px; font-weight: bold; text-anchor: middle; dominant-baseline: central; }
</style>
</head>
<body>
<div class="diagram-container">
<svg viewBox="0 0 1050 480" width="1050" height="480" style="display: block; margin: 20px auto; padding: 20px;" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#8b949e"/>
    </marker>
  </defs>

  <!-- Lines -->
  <line x1="130" y1="210" x2="155" y2="210" class="line" /> <!-- Human -> PM -->
  <line x1="280" y1="210" x2="305" y2="210" class="line" /> <!-- PM -> Arch -->
  <line x1="430" y1="210" x2="455" y2="210" class="line" /> <!-- Arch -> Coding -->
  <line x1="580" y1="210" x2="605" y2="210" class="line" /> <!-- Coding -> Review -->
  
  <!-- Review to Awaiting (2) -->
  <path d="M 710 180 Q 735 80 755 80" class="line" />
  <circle cx="732" cy="115" r="8" class="circ"/>
  <text x="732" y="115" class="circ-text">2</text>

  <!-- Review to Blocked (3) -->
  <line x1="730" y1="210" x2="755" y2="210" class="line" />
  <circle cx="745" cy="210" r="8" class="circ"/>
  <text x="745" y="210" class="circ-text">3</text>

  <!-- Coding -> Testing -->
  <line x1="520" y1="180" x2="520" y2="115" class="line" />
  <!-- Testing -> Review -->
  <path d="M 580 80 Q 670 80 670 175" class="line" />

  <!-- Review to Coding (1) -->
  <path d="M 630 240 Q 595 270 560 240" class="line" />
  <circle cx="595" cy="255" r="8" class="circ"/>
  <text x="595" y="255" class="circ-text">1</text>
  
  <!-- Awaiting -> Git (4) -->
  <line x1="880" y1="80" x2="905" y2="80" class="line" />
  <circle cx="895" cy="80" r="8" class="circ"/>
  <text x="895" y="80" class="circ-text">4</text>

  <!-- Blocked -> Manager -->
  <line x1="820" y1="240" x2="820" y2="305" class="line" />

  <!-- Manager -> Reflection (5) -->
  <line x1="880" y1="340" x2="905" y2="340" class="line" />
  <circle cx="895" cy="340" r="8" class="circ"/>
  <text x="895" y="340" class="circ-text">5</text>

  <!-- Reflection -> Coding (6) -->
  <path d="M 970 370 C 970 480, 520 480, 520 245" class="line" />
  <circle cx="745" cy="455" r="8" class="circ"/>
  <text x="745" y="455" class="circ-text">6</text>

  <!-- Boxes -->
  <!-- Top Row -->
  <rect id="agent_testing" x="460" y="50" width="120" height="60" class="box" fill="#22c55e" />
  <text x="520" y="72" class="text">Testing</text><text x="520" y="88" class="text">Agent</text>

  <rect x="760" y="50" width="120" height="60" class="box" fill="#1f2937" />
  <text x="820" y="72" class="text">Awaiting Human</text><text x="820" y="88" class="text">Approval</text>

  <rect x="910" y="50" width="120" height="60" class="box" fill="#166534" />
  <text x="970" y="72" class="text">git commit</text><text x="970" y="88" class="text">in sample repo</text>

  <!-- Middle Row -->
  <rect x="10" y="180" width="120" height="60" class="box" fill="#1f2937" />
  <text x="70" y="210" class="text">Human Request</text>

  <rect id="agent_pm" x="160" y="180" width="120" height="60" class="box" fill="#3b82f6" />
  <text x="220" y="210" class="text">PM Agent</text>

  <rect id="agent_architect" x="310" y="180" width="120" height="60" class="box" fill="#8b5cf6" />
  <text x="370" y="202" class="text">Architect</text><text x="370" y="218" class="text">Agent</text>

  <rect id="agent_coding" x="460" y="180" width="120" height="60" class="box" fill="#f97316" />
  <text x="520" y="210" class="text">Coding Agent</text>

  <rect id="agent_review" x="610" y="180" width="120" height="60" class="box" fill="#ef4444" />
  <text x="670" y="210" class="text">Review Agent</text>

  <rect x="760" y="180" width="120" height="60" class="box" fill="#7f1d1d" />
  <text x="820" y="210" class="text">Blocked</text>

  <!-- Bottom Row -->
  <rect id="agent_manager" x="760" y="310" width="120" height="60" class="box" fill="#6366f1" />
  <text x="820" y="332" class="text">Manager Agent</text><text x="820" y="348" class="text">(Pure Python)</text>

  <rect id="agent_reflection" x="910" y="310" width="120" height="60" class="box" fill="#ec4899" />
  <text x="970" y="332" class="text">Reflection Agent</text><text x="970" y="348" class="text">(Rewrites prompt)</text>

  <!-- Legend -->
  <rect x="10" y="290" width="600" height="170" fill="transparent" stroke="#30363d" stroke-width="2" rx="8" />
  
  <circle cx="40" cy="325" r="10" class="circ"/><text x="40" y="325" class="circ-text" style="font-size:12px;">1</text>
  <text x="65" y="325" class="leg-text">failed &lt; 2 retries</text>
  
  <circle cx="40" cy="375" r="10" class="circ"/><text x="40" y="375" class="circ-text" style="font-size:12px;">2</text>
  <text x="65" y="375" class="leg-text">passed</text>
  
  <circle cx="40" cy="425" r="10" class="circ"/><text x="40" y="425" class="circ-text" style="font-size:12px;">3</text>
  <text x="65" y="425" class="leg-text">failed ≥ 2</text>

  <circle cx="280" cy="325" r="10" class="circ"/><text x="280" y="325" class="circ-text" style="font-size:12px;">4</text>
  <text x="305" y="325" class="leg-text">Approved</text>
  
  <circle cx="280" cy="375" r="10" class="circ"/><text x="280" y="375" class="circ-text" style="font-size:12px;">5</text>
  <text x="305" y="375" class="leg-text">rate &lt; 60% &amp; runs ≥ 3</text>
  
  <circle cx="280" cy="425" r="10" class="circ"/><text x="280" y="425" class="circ-text" style="font-size:12px;">6</text>
  <text x="305" y="425" class="leg-text">rewrites prompt via LLM</text>
</svg>
</div>
</body>
</html>
"""
    if active_agent:
        # Wrap the rect with a <g> that contains a tooltip, and add active-beep class
        target_str = f'<rect id="agent_{active_agent}"'
        replacement = f'<g><title>Currently Active Agent</title><rect id="agent_{active_agent}" class="box active-beep"'
        # Need to fix the closing tag for the group. Actually, replacing the exact tag is hard without regex.
        # Let's just use replace with regex or simpler string replacement since we know they end with "/>"
        import re
        # Find the specific rect tag and wrap it
        pattern = f'(<rect id="agent_{active_agent}"[^>]*/>)'
        html = re.sub(pattern, r'<g><title>Currently Active: ' + active_agent.upper() + r'</title></g>', html)
        html = html.replace(f'id="agent_{active_agent}" class="box"', f'id="agent_{active_agent}" class="box active-beep"')
        
    return html

# We will use st.empty() to allow live updating of the diagram!
svg_placeholder = st.empty()
with svg_placeholder:
    components.html(get_svg_html(), height=450, scrolling=True)

col_main, col_side = st.columns([2, 1])

with col_main:
    # --- MANAGER AGENT STATS GRAPH ---
    import pandas as pd
    import plotly.express as px
    stats_path = os.path.join(_REPO_ROOT, "agents", "manager_agent", "agent_stats.json")
    if os.path.exists(stats_path):
        with st.expander("📊 Agent Performance", expanded=False):
            st.markdown("**(Compare Previous vs Current Rate to see Reflection Agent improvements)**")
            try:
                with open(stats_path, "r", encoding="utf-8") as f:
                    stats = json.load(f)

                chart_data = {"Agent": [], "Previous Rate (%)": [], "Current Rate (%)": []}
                for agent, data in stats.items():
                    if "rate" in data and data["rate"] is not None:
                        agent_name = agent.replace("_agent", "").title()
                        if agent_name == "Pm":
                            agent_name = "PM"
                        elif agent_name == "Architect":
                            agent_name = "Architecture"
                        chart_data["Agent"].append(agent_name)

                        # Fallback to current rate if previous_rate is None
                        prev_rate = data.get("previous_rate")
                        if prev_rate is None:
                            prev_rate = data["rate"]

                        chart_data["Previous Rate (%)"].append(prev_rate * 100)
                        chart_data["Current Rate (%)"].append(data["rate"] * 100)

                if chart_data["Agent"]:
                    df = pd.DataFrame(chart_data)
                    # Melt data for plotly grouped bar
                    df_melted = df.melt(id_vars="Agent", var_name="Rate Type", value_name="Rate (%)")

                    fig = px.bar(
                        df_melted, x="Agent", y="Rate (%)", color="Rate Type", barmode="group",
                        text="Rate (%)",
                        color_discrete_map={"Previous Rate (%)": "#30363d", "Current Rate (%)": "#2ea043"},
                        height=450
                    )

                    fig.update_traces(texttemplate='%{text:.0f}%', textposition='outside', textfont_color='white')

                    # Configure legend and styling
                    fig.update_layout(
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, title=None),
                        margin=dict(l=20, r=20, t=25, b=20),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#c9d1d9"),
                        hovermode="x unified"
                    )

                    # Y-axis ticks: markers every 10, labels every 20
                    tick_vals = list(range(0, 101, 10))
                    tick_text = [str(v) if v % 20 == 0 else "" for v in tick_vals]
                    fig.update_yaxes(
                        tickmode="array",
                        tickvals=tick_vals,
                        ticktext=tick_text,
                        range=[0, 115],
                        gridcolor="rgba(88, 166, 255, 0.1)",
                        zerolinecolor="rgba(88, 166, 255, 0.3)",
                        title=""
                    )
                    fig.update_xaxes(title="")

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Not enough data to plot stats yet.")
            except Exception as e:
                st.info(f"Stats could not be loaded: {e}")

    key_suffix = st.session_state.form_reset_counter

    # Fixed project directory (not user-editable)
    target_repo = "sample_repo/flaskbb"

    st.markdown("<p><b>ENTER REQUESTS:-</b></p>", unsafe_allow_html=True)

    user_request = st.text_area("Request", key=f"req_{key_suffix}", label_visibility="collapsed", value=loaded_req, placeholder="create a testers.py that prints hi", height=140)

    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

    # Run Button
    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    run_clicked = st.button("🚀 RUN PIPELINE", type="primary", use_container_width=True)

with col_side:
    st.markdown("<p><b>CURRENT RUN</b></p>", unsafe_allow_html=True)
    status_panel = st.empty()
    
    if st.session_state.last_run_stats:
        stats = st.session_state.last_run_stats
        if stats.get("status") == "success":
            color = "#2ea043"
            header = "✓ Completed"
            shadow = "rgba(46,160,67,0.1)"
        else:
            color = "#f85149"
            header = "❌ Failed / Code not generated"
            shadow = "rgba(248,81,73,0.1)"
            
        tid = stats.get("tid", "Unknown")
            
        status_panel.markdown(f"""
        <div style='background: rgba(22, 27, 34, 0.5); padding: 20px; border-radius: 12px; border: 1px solid {color}; font-family: monospace; color: #c9d1d9; box-shadow: 0 4px 15px {shadow};'>
            <div style='margin-bottom: 12px; color: #00ccff; font-weight: bold;'>Task_id: {tid}</div>
            <div style='color: {color}; font-weight: bold; margin-bottom: 15px;'>{header}</div>
            <div style='margin-bottom: 8px;'><span style='color: #8b949e; display: inline-block; width: 120px;'>Agents used</span> {stats['agents_used']}</div>
            <div style='margin-bottom: 8px;'><span style='color: #8b949e; display: inline-block; width: 120px;'>Attempts</span> {stats['attempts']}</div>
            <div style='margin-bottom: 8px;'><span style='color: #8b949e; display: inline-block; width: 120px;'>Files created</span> {stats['files_created']}</div>
            <div style='margin-bottom: 8px;'><span style='color: #8b949e; display: inline-block; width: 120px;'>Tests passed</span> {stats['tests_passed']}</div>
            <div><span style='color: #8b949e; display: inline-block; width: 120px;'>Total time</span> {stats['time']}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        status_panel.markdown("""
        <div style='background: rgba(22, 27, 34, 0.5); padding: 20px; border-radius: 12px; border: 1px solid #30363d; font-family: monospace; color: #c9d1d9; box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
            <div style='margin-bottom: 8px;'><span style='color: #8b949e; display: inline-block; width: 80px;'>Status</span> No prompt Given</div>
            <div style='margin-bottom: 8px;'><span style='color: #8b949e; display: inline-block; width: 80px;'>Elapsed</span> 0 sec</div>
            <div><span style='color: #8b949e; display: inline-block; width: 80px;'>Files</span> None</div>
        </div>
        """, unsafe_allow_html=True)

if run_clicked:
    with col_main:
        # Auto-generate a unique task ID
        tid_clean = f"task_{_uuid.uuid4().hex[:6]}"

        if not user_request.strip():
            st.error("Please enter a feature request first.")
        else:
            st.session_state.last_run_stats = None
            st.info(f"Running pipeline for: *{user_request.strip()[:80]}...*")
            
            start_time = time.time()
            current_files = "None"
            last_panel_update = [0] # List to allow modification in inner scope
            
            # Dynamic stats tracking
            active_agents = set()
            total_attempts = 1
            files_created_count = 0
            tests_passed_str = "0/0"


            def update_status_panel():
                elapsed = f"{time.time() - start_time:.1f} sec"
                status_panel.markdown(f"""
                <div style='background: rgba(22, 27, 34, 0.5); padding: 20px; border-radius: 12px; border: 1px solid #30363d; font-family: monospace; color: #c9d1d9; box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
                    <div style='margin-bottom: 12px; color: #00ccff; font-weight: bold;'>Task_id: {tid_clean}</div>
                    <div style='margin-bottom: 8px;'><span style='color: #8b949e; display: inline-block; width: 80px;'>Status</span> Running</div>
                    <div style='margin-bottom: 8px;'><span style='color: #8b949e; display: inline-block; width: 80px;'>Elapsed</span> {elapsed}</div>
                    <div><span style='color: #8b949e; display: inline-block; width: 80px;'>Files</span> {current_files}</div>
                </div>
                """, unsafe_allow_html=True)

            update_status_panel()
            
            cmd = [
                sys.executable, "-u", "orchestration/pipeline.py",
                "--repo", target_repo,
                "--request", user_request.strip(),
                "--username", current_username,
                "--task-id", tid_clean,
            ]

            with st.status("🚀 AI Dev Team at work...", expanded=True) as status_box:
                pm_ph = st.empty()
                arch_ph = st.empty()
                code_ph = st.empty()
                test_ph = st.empty()
                review_ph = st.empty()
                manager_ph = st.empty()

                log_expander = st.expander("📜 Live Terminal Stream", expanded=False)
                log_box = log_expander.empty()
                captured_lines = []
                agent_streams = {}

                try:
                    proc = subprocess.Popen(
                        cmd, cwd=_REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        universal_newlines=True, encoding="utf-8", bufsize=1
                    )
                    for line in iter(proc.stdout.readline, ""):
                        if time.time() - last_panel_update[0] > 0.5:
                            update_status_panel()
                            last_panel_update[0] = time.time()
                        
                        captured_lines.append(line)
                        log_box.code("".join(captured_lines), language="text")

                        # Handle structured agent events for real-time thinking & output
                        if line.startswith("@@AGENT_EVENT@@"):
                            try:
                                ev = json.loads(line.replace("@@AGENT_EVENT@@", "").strip())
                                agent = ev.get("agent")
                                ev_type = ev.get("type")
                                msg = ev.get("message", "")
                                data = ev.get("data", {})
                                
                                if agent: active_agents.add(agent)
                                if ev_type == "retry": total_attempts += 1
                                
                                # Update SVG dynamically
                                if agent:
                                    # Normalize agent name for SVG IDs
                                    clean_agent = agent.replace("_agent", "")
                                    if clean_agent == "architecture": clean_agent = "architect"
                                    with svg_placeholder:
                                        components.html(get_svg_html(clean_agent), height=450, scrolling=True)

                                if agent == "pm_agent":
                                    if ev_type == "start":
                                        pm_ph.info(f"🧠 **PM Agent** ⏳ *{msg}*")
                                    elif ev_type == "done":
                                        with pm_ph.container():
                                            st.markdown("#### 🧠 PM Agent ✅ *Acceptance Criteria Defined*")
                                            user_story = data.get("user_story")
                                            if user_story:
                                                st.caption(f"**User Story:** {user_story}")
                                            criteria = data.get("acceptance_criteria", [])
                                            for c in criteria:
                                                st.markdown(f"- ✅ {c}")
                                    elif ev_type == "error":
                                        pm_ph.error(f"🧠 **PM Agent** ❌ {msg}")

                                elif agent == "architect_agent":
                                    if ev_type == "start":
                                        arch_ph.info(f"📐 **Architect Agent** ⏳ *{msg}*")
                                    elif ev_type == "retry":
                                        arch_ph.warning(f"📐 **Architect Agent** ⚠️ *{msg}*")
                                    elif ev_type == "done":
                                        with arch_ph.container():
                                            st.markdown("#### 📐 Architect Agent ✅ *Architecture Plan & Scope*")
                                            scoped = data.get("scoped_files", [])
                                            if scoped:
                                                current_files = ", ".join(scoped)
                                                update_status_panel()
                                                st.markdown("**Scoped Files:** " + " ".join([f"`{f}`" for f in scoped]))
                                            plan = data.get("plan", "")
                                            if plan:
                                                with st.expander("📋 View Architectural Plan", expanded=False):
                                                    st.markdown(plan)
                                    elif ev_type == "error":
                                        arch_ph.error(f"📐 **Architect Agent** ❌ {msg}")

                                elif agent == "coding_agent":
                                    if ev_type == "start":
                                        code_ph.info(f"💻 **Coding Agent** ⏳ *{msg}*")
                                    elif ev_type == "retry":
                                        code_ph.warning(f"💻 **Coding Agent** ⚠️ *{msg}*")
                                    elif ev_type == "done":
                                        with code_ph.container():
                                            st.markdown("#### 💻 Coding Agent ✅ *Unified Diff Generated & Verified*")
                                            diff = data.get("code_diff", "")
                                            if diff:
                                                files_created_count = diff.count("+++ ")
                                                with st.expander("💻 View Generated Code Diff", expanded=True):
                                                    st.code(diff, language="diff")
                                    elif ev_type == "error":
                                        code_ph.error(f"💻 **Coding Agent** ❌ {msg}")

                                elif agent == "testing_agent":
                                    if ev_type == "start":
                                        test_ph.info(f"🧪 **Testing Agent** ⏳ *{msg}*")
                                    elif ev_type == "done":
                                        with test_ph.container():
                                            passed = data.get("passed", False)
                                            badge = "✅ *Tests Passed*" if passed else "⚠️ *Test Issues Detected*"
                                            st.markdown(f"#### 🧪 Testing Agent {badge}")
                                            matched = data.get("criteria_matched", [])
                                            failures = data.get("failures", [])
                                            total_tests = len(matched) + len(failures)
                                            tests_passed_str = f"{len(matched)}/{total_tests}" if total_tests > 0 else "0/0"
                                            if matched:
                                                st.markdown(f"**Verified Criteria ({len(matched)}):**")
                                                for m in matched:
                                                    st.markdown(f"- ✔️ {m}")
                                            if failures:
                                                st.error("**Failures / Notes:**\n" + "\n".join([f"- {f}" for f in failures]))
                                    elif ev_type == "error":
                                        test_ph.error(f"🧪 **Testing Agent** ❌ {msg}")

                                elif agent == "review_agent":
                                    if ev_type == "start":
                                        review_ph.info(f"🛡️ **Review Agent** ⏳ *{msg}*")
                                    elif ev_type == "done":
                                        with review_ph.container():
                                            passed = data.get("passed", False)
                                            risk = str(data.get("risk_level", "low")).upper()
                                            badge = f"✅ *Approved (Risk: {risk})*" if passed else f"⚠️ *Review Complete (Risk: {risk})*"
                                            st.markdown(f"#### 🛡️ Review Agent {badge}")
                                            findings = data.get("findings", [])
                                            if findings:
                                                for f in findings:
                                                    st.warning(f"**[{f.get('severity', 'finding').upper()}]** {f.get('description', '')}")
                                            else:
                                                st.success("Zero high-severity security findings detected.")
                                    elif ev_type == "error":
                                        review_ph.error(f"🛡️ **Review Agent** ❌ {msg}")

                                elif agent == "manager_agent":
                                    if ev_type == "done":
                                        with manager_ph.container():
                                            st.markdown("#### 📊 Manager Agent & Consensus Arbiter")
                                            c_report = data.get("consensus_report") or {}
                                            score = c_report.get("consensus_score_pct", 0)
                                            conf = c_report.get("confidence_level", "NORMAL")
                                            st.metric(label="Multi-Agent Consensus Confidence", value=f"{score}%", delta=conf)

                            except Exception:
                                pass

                        elif line.startswith("@@AGENT_STREAM@@"):
                            try:
                                ev = json.loads(line.replace("@@AGENT_STREAM@@", "").strip())
                                agent = ev.get("agent")
                                chunk = ev.get("chunk", "")

                                agent_streams[agent] = agent_streams.get(agent, "") + chunk
                                stream_text = agent_streams[agent]

                                if agent == "pm_agent":
                                    pm_ph.info(f"🧠 **PM Agent** (Thinking...)\n```json\n{stream_text}\n```")
                                elif agent == "architect_agent":
                                    arch_ph.info(f"📐 **Architect Agent** (Thinking...)\n```json\n{stream_text}\n```")
                                elif agent == "coding_agent":
                                    code_ph.info(f"💻 **Coding Agent** (Thinking...)\n```diff\n{stream_text}\n```")
                                elif agent == "testing_agent":
                                    test_ph.info(f"🧪 **Testing Agent** (Thinking...)\n```json\n{stream_text}\n```")
                                elif agent == "review_agent":
                                    review_ph.info(f"🛡️ **Review Agent** (Thinking...)\n```json\n{stream_text}\n```")
                            except Exception:
                                pass

                    proc.wait()

                    is_success = (proc.returncode == 0 and files_created_count > 0)
                    
                    final_time = f"{time.time() - start_time:.1f} sec"
                    st.session_state.last_run_stats = {
                        "tid": tid_clean,
                        "status": "success" if is_success else "error",
                        "agents_used": len(active_agents) if active_agents else 1,
                        "attempts": total_attempts,
                        "files_created": files_created_count,
                        "tests_passed": tests_passed_str,
                        "time": final_time
                    }
                    
                    
                    # Explicitly save stats to task json so history is perfectly accurate
                    task_file_path = os.path.join(_USER_TASKS_DIR, f"{tid_clean}.json")
                    try:
                        if os.path.exists(task_file_path):
                            with open(task_file_path, "r", encoding="utf-8") as tf:
                                t_data = json.load(tf)
                        else:
                            t_data = {
                                "task_id": tid_clean,
                                "feature_request": user_request.strip(),
                                "status": "failed",
                                "history": [],
                                "code_diff": None,
                                "plan": None
                            }
                        t_data["run_stats"] = st.session_state.last_run_stats
                        with open(task_file_path, "w", encoding="utf-8") as tf:
                            json.dump(t_data, tf, indent=2)
                        st.session_state.selected_task_file = task_file_path
                    except Exception:
                        pass
                        
                    if is_success:
                        status_box.update(label="✅ Pipeline Completed Successfully!", state="complete", expanded=True)
                        st.success("✅ Pipeline completed successfully! Refreshing UI...")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        status_box.update(label="❌ Pipeline Finished with an Issue (Code not generated)", state="error", expanded=True)
                        st.error("❌ Pipeline finished with an error or failed to generate code. Check the logs above.")
                        time.sleep(1.5)
                        st.rerun()

                except Exception as e:
                    st.error(f"Failed to start pipeline: {e}")

st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Generated Code Viewer — shown for loaded historical tasks
# ---------------------------------------------------------------------------
def _render_code_viewer(code_diff, section_title="📄 Generated Code"):
    """Render the generated code viewer with tabs and download buttons."""
    generated_files = _extract_generated_code(code_diff)
    if not generated_files:
        st.info("No generated Python code to display for this task.")
        return

    st.markdown(f"<div class='code-viewer-title'>{section_title}</div>", unsafe_allow_html=True)

    if len(generated_files) == 1:
        fname, code = list(generated_files.items())[0]
        st.markdown(f"**`{fname}`**")
        st.code(code, language="python")
        st.download_button(
            label=f"⬇ Download {fname}",
            data=code,
            file_name=fname,
            mime="text/x-python",
            key=f"dl_{fname}_{hash(code) % 10000}",
        )
    else:
        tab_labels = [f"📄 {fname}" for fname in generated_files.keys()]
        tabs = st.tabs(tab_labels)
        for tab, (fname, code) in zip(tabs, generated_files.items()):
            with tab:
                st.code(code, language="python")
                st.download_button(
                    label=f"⬇ Download {fname}",
                    data=code,
                    file_name=fname,
                    mime="text/x-python",
                    key=f"dl_{fname}_{hash(code) % 10000}",
                )


# Display historical data if selected
if st.session_state.get("selected_task_file") and loaded_task_data:
    st.markdown("---")
    
    hist_col_main, hist_col_side = st.columns([2, 1])
    
    with hist_col_main:
        st.markdown(f"### 🕒 History for Task: `{loaded_tid}`")
        tab1, tab2, tab3 = st.tabs(["📄 Generated Code", "💻 Code Diff", "📋 Architect Plan"])
        
        with tab1:
            if loaded_diff:
                _render_code_viewer(loaded_diff, section_title="Generated Python Code")
            else:
                st.info("No generated code available for this task.")

        with tab2:
            if loaded_diff:
                st.download_button(
                    label="⬇ Download Diff (.patch)",
                    data=loaded_diff,
                    file_name=f"{loaded_tid}.patch",
                    mime="text/x-patch",
                    use_container_width=True,
                )
                st.code(loaded_diff, language="diff")
            else:
                st.info("No code changes were generated for this task.")
                
        with tab3:
            if loaded_plan:
                st.markdown(loaded_plan)
            else:
                st.info("No architectural plan was generated.")

    with hist_col_side:
        st.markdown("<p><b>HISTORICAL RUN</b></p>", unsafe_allow_html=True)
        if loaded_task_data:
            saved_stats = loaded_task_data.get("run_stats")
            
            if saved_stats:
                h_agents = saved_stats.get("agents_used", 1)
                h_attempts = saved_stats.get("attempts", 1)
                h_files_created = saved_stats.get("files_created", 0)
                h_tests_passed = saved_stats.get("tests_passed", "0/0")
                h_time = saved_stats.get("time", "N/A")
                is_h_success = (saved_stats.get("status") == "success")
            else:
                # Fallback for old tasks
                h_history = loaded_task_data.get("history", [])
                h_agents = len(set(h["agent"] for h in h_history if "agent" in h)) if h_history else 1
                h_attempts = 1 + loaded_task_data.get("retry_count", 0)
                h_diff = loaded_task_data.get("code_diff", "")
                h_files_created = h_diff.count("+++ ") if h_diff else 0
                h_tests = loaded_task_data.get("test_results") or {}
                if isinstance(h_tests, dict):
                    matched = len(h_tests.get("criteria_matched", []))
                    failed = len(h_tests.get("failures", []))
                    h_tests_passed = f"{matched}/{matched+failed}" if (matched+failed) > 0 else "0/0"
                else:
                    h_tests_passed = "0/0"
                is_h_success = (h_files_created > 0)
                h_time = "N/A"

            
            if is_h_success:
                color = "#2ea043"
                header = "✓ Completed"
                shadow = "rgba(46,160,67,0.1)"
            else:
                color = "#f85149"
                header = "❌ Failed / Code not generated"
                shadow = "rgba(248,81,73,0.1)"
                
            st.markdown(f"""
            <div style='background: rgba(22, 27, 34, 0.5); padding: 20px; border-radius: 12px; border: 1px solid {color}; font-family: monospace; color: #c9d1d9; box-shadow: 0 4px 15px {shadow};'>
                <div style='margin-bottom: 12px; color: #00ccff; font-weight: bold;'>Task_id: {loaded_tid}</div>
                <div style='color: {color}; font-weight: bold; margin-bottom: 15px;'>{header}</div>
                <div style='margin-bottom: 8px;'><span style='color: #8b949e; display: inline-block; width: 120px;'>Agents used</span> {h_agents}</div>
                <div style='margin-bottom: 8px;'><span style='color: #8b949e; display: inline-block; width: 120px;'>Attempts</span> {h_attempts}</div>
                <div style='margin-bottom: 8px;'><span style='color: #8b949e; display: inline-block; width: 120px;'>Files created</span> {h_files_created}</div>
                <div style='margin-bottom: 8px;'><span style='color: #8b949e; display: inline-block; width: 120px;'>Tests passed</span> {h_tests_passed}</div>
                <div><span style='color: #8b949e; display: inline-block; width: 120px;'>Total time</span> {h_time}</div>
            </div>
            """, unsafe_allow_html=True)

# --- HUMAN APPROVAL SECTION ---
pending_tasks = []
for f in task_files:
    try:
        with open(f, "r", encoding="utf-8") as f_in:
            data = json.load(f_in)
            if data.get("status") == "awaiting_human_approval" and data.get("code_diff"):
                pending_tasks.append((f, data))
    except json.JSONDecodeError:
        st.sidebar.error(f"⚠️ Failed to parse pending task: {os.path.basename(f)}")
    except Exception:
        pass

@st.dialog("👀 Action Required: Human Approval")
def review_modal(f_path, t_data):
    tid = t_data.get("task_id", "Unknown")
    freq = t_data.get("feature_request", "")
    diff = t_data.get("code_diff", "")
    
    st.markdown(f"**Task:** {tid}")
    st.markdown(f"**Request:** *{freq}*")
    st.code(diff, language="diff")
    
    st.markdown("---")
    acol1, acol2 = st.columns(2)
    with acol1:
        st.markdown('<div class="approve-btn">', unsafe_allow_html=True)
        if st.button("✅ Approve & Apply", key=f"approve_{tid}", use_container_width=True):
            t_data["status"] = "approved"
            with open(f_path, "w", encoding="utf-8") as f_out:
                json.dump(t_data, f_out, indent=2)
            
            with st.spinner(f"Applying fixes for {tid}..."):
                apply_cmd = [
                    sys.executable, "orchestration/apply_fixes.py",
                    "--repo", target_repo,
                    "--tasks-dir", _USER_TASKS_DIR,
                ]
                try:
                    res = subprocess.run(apply_cmd, cwd=_REPO_ROOT, capture_output=True, text=True)
                    if res.returncode == 0:
                        st.success("Changes applied successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Failed to apply fixes:\n{res.stderr}")
                except Exception as e:
                    st.error(f"Error executing apply_fixes.py: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with acol2:
        st.markdown('<div class="reject-btn">', unsafe_allow_html=True)
        if st.button("❌ Reject", key=f"reject_{tid}", use_container_width=True):
            t_data["status"] = "rejected"
            with open(f_path, "w", encoding="utf-8") as f_out:
                json.dump(t_data, f_out, indent=2)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if pending_tasks:
    # Pop up the dialog for the first pending task automatically
    f_path, t_data = pending_tasks[0]
    review_modal(f_path, t_data)
