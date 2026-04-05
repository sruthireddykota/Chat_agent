import streamlit as st
from pathlib import Path
from config.settings import settings
from utils.file_browser import _collect_files, _render_content, LANG_MAP
from PIL import Image

workspace_icon = Image.open("assets/robot.png")

st.set_page_config(
    page_title="Workspace Explorer",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="collapsed",  
)

st.markdown("""
<style>
    [data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

#Sidebar navigation
with st.sidebar:
    s_col1, s_col2 = st.columns([5, 5])
    with s_col1:
        if st.button("🏠︎ Home", key="back_to_home", help="Back to Dashboard"):
            st.switch_page("main.py")
    with s_col2:
        if st.button("💬 Chat", key="back_to_chat", help="Back to Chat"):
            st.switch_page("pages/chatbot.py")

# Guard: must be Coder agent with an active session 
if st.session_state.get("selected_agent") != "Coder":
    st.warning("Workspace Explorer is only available when the Coder agent is active.")
    st.stop()

session_id = st.session_state.get("current_session")
if not session_id:
    st.error("No active session found. Go back to Chat and start a session.")
    st.stop()

workspace = f"{settings.CODER_BASE_PATH}/{session_id}"
ws = Path(workspace)

# Page title 
st.title("Workspace Explorer", text_alignment="center")

files = _collect_files(workspace)
if not files:
    st.info("No files in this workspace yet. Run the Coder agent to generate files.")
    st.stop()

labels = [str(f.relative_to(ws)) for f in files]

# State scoped to this session 
EXP_SEL = f"exp_sel_{session_id}"
if EXP_SEL not in st.session_state:
    st.session_state[EXP_SEL] = None

# Layout: narrow tree | wide preview
tree_col, preview_col = st.columns([1, 3], gap="medium")

with tree_col:
    with st.container(height=620, border=True):
        st.markdown("**Files**")

        # Group files by folder for a tree feel
        grouped: dict[str, list[str]] = {}
        for label in labels:
            parts  = Path(label).parts
            folder = str(Path(*parts[:-1])) if len(parts) > 1 else "."
            grouped.setdefault(folder, []).append(label)

        for folder, folder_files in grouped.items():
            if folder != ".":
                st.markdown(
                    f"<span style='font-size:0.75rem;color:gray;'>📁 {folder}</span>",
                    unsafe_allow_html=True,
                )
            for label in folder_files:
                ext = Path(label).suffix.lower()
                is_sel = st.session_state[EXP_SEL] == label

                if st.button(
                    f"{Path(label).name}",
                    key=f"exp_{session_id}_{label}",
                    use_container_width=True,
                    type="primary" if is_sel else "secondary",
                    help=label):
                    st.session_state[EXP_SEL] = label

with preview_col:
    sel = st.session_state[EXP_SEL]

    if sel is None:
        with st.container(height=620, border=True):
            st.markdown(
                """<div style="height:620px;display:flex;flex-direction:column;
                    align-items:center;justify-content:center;opacity:0.3;gap:12px;">
                    <span style="font-size:3rem;">📂</span>
                    <span>Select a file from the tree to preview</span>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        sel_path = ws / sel
        if not sel_path.exists():
            st.session_state[EXP_SEL] = None
            st.warning("File no longer exists — select another.")
        else:
            ext = sel_path.suffix.lower()
            lang_label, lang_hint = LANG_MAP.get(ext, ("File", ""))

            # ── File header bar
            hdr1, hdr2, hdr3 = st.columns([2, 1, 1])
            hdr1.markdown(
                f"**{sel}** &nbsp;"
                f"<span style='background:#e8f0fe;color:#1a56db;"
                f"padding:2px 8px;border-radius:4px;font-size:0.75rem;'>"
                f"{lang_label}</span>",
                unsafe_allow_html=True,
            )
            hdr2.download_button(
                label="⬇ Download",
                data=sel_path.read_bytes(),
                file_name=sel_path.name,
                mime="text/plain",
                key=f"exp_dl_{session_id}_{sel}",
                use_container_width=True,
            )
            file_size = sel_path.stat().st_size
            hdr3.markdown(
                f"<div style='padding-top:6px;font-size:0.8rem;"
                f"color:gray;text-align:right;'>{file_size:,} bytes</div>",
                unsafe_allow_html=True,
            )
            st.divider()

            with st.container(height=560, border=False):
                _render_content(sel_path, ext, lang_hint)