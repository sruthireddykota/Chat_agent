import os
import streamlit as st
from pathlib import Path

LANG_MAP = {
    ".py":   ("Python",       "python"),
    ".sql":  ("SQL",          "sql"),
    ".md":   ("Markdown",     "markdown"),
    ".txt":  ("Text",         ""),
    ".json": ("JSON",         "json"),
    ".yaml": ("YAML",         "yaml"),
    ".yml":  ("YAML",         "yaml"),
    ".sh":   ("Shell",        "bash"),
    ".toml": ("TOML",         "toml"),
    ".csv":  ("CSV",          ""),
    ".html": ("HTML",         "html"),
    ".js":   ("JavaScript",   "javascript"),
}


def _collect_files(workspace: str) -> list[Path]:
    skip = {"__pycache__", ".git", "__init__", "node_modules", ".venv"}
    result = []
    for root, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in sorted(files):
            result.append(Path(root) / f)
    return sorted(result)


def render_file_browser(workspace: str, session_id: str):
    """
    Inline file browser — rendered only after agent response completes.
    Scoped entirely to session_id so switching chats never bleeds state.
    """
    files = _collect_files(workspace)
    if not files:
        st.info("No files generated yet in this session.")
        return

    ws = Path(workspace)
    labels = [str(f.relative_to(ws)) for f in files]
    sel_key = f"fb_sel_{session_id}"

    # Always initialise — never carry over from a different session
    if sel_key not in st.session_state:
        st.session_state[sel_key] = None

    with st.container(border=True):
        st.markdown("##### Workspace files")
        left_col, right_col = st.columns([1, 4], gap="medium")

        # file list
        with left_col:
            with st.container(height=400, border=False):
                for label in labels:
                    ext      = Path(label).suffix.lower()
                    selected = st.session_state[sel_key] == label

                    if st.button(
                        f"{label}",
                        key=f"fb_{session_id}_{label}",
                        use_container_width=True,
                        type="primary" if selected else "secondary",
                    ):
                        st.session_state[sel_key] = label

        # preview pane
        with right_col:
            with st.container(height=400, border=True):
                sel = st.session_state[sel_key]

                if sel is None:
                    st.markdown(
                        """<div style="height:340px;display:flex;flex-direction:column;
                            align-items:center;justify-content:center;opacity:0.35;gap:10px;">
                            <span style="font-size:2.5rem;">📂</span>
                            <span style="font-size:0.9rem;">Select a file to preview</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                else:
                    sel_path = ws / sel
                    if not sel_path.exists():
                        st.session_state[sel_key] = None
                        st.warning("File no longer exists — select another.")
                    else:
                        ext = sel_path.suffix.lower()
                        lang_label, lang_hint = LANG_MAP.get(ext, ("File", ""))

                        h1, h2 = st.columns([3, 1])
                        h1.markdown(
                            f"**{sel}** &nbsp;"
                            f"<span style='background:#e8f0fe;color:#1a56db;"
                            f"padding:2px 8px;border-radius:4px;font-size:0.75rem;'>"
                            f"{lang_label}</span>",
                            unsafe_allow_html=True,
                        )
                        h2.download_button(
                            label="⬇ Download",
                            data=sel_path.read_bytes(),
                            file_name=sel_path.name,
                            mime="text/plain",
                            key=f"fb_dl_{session_id}_{sel}",
                            use_container_width=True,
                        )
                        st.divider()
                        _render_content(sel_path, ext, lang_hint)


def _render_content(path: Path, ext: str, lang_hint: str):
    if ext == ".csv":
        try:
            import pandas as pd
            st.dataframe(pd.read_csv(path), use_container_width=True)
        except Exception as e:
            st.warning(f"Could not load CSV: {e}")
    elif ext == ".md":
        try:
            st.markdown(path.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            st.warning(f"Could not render Markdown: {e}")
    elif lang_hint:
        try:
            st.code(path.read_text(encoding="utf-8", errors="replace"), language=lang_hint)
        except Exception as e:
            st.warning(f"Could not preview: {e}")
    elif ext in LANG_MAP:
        try:
            st.text(path.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            st.warning(f"Could not read file: {e}")
    else:
        st.info("Binary file — use the download button above.")