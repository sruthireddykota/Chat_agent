import streamlit as st
import pandas as pd
import asyncio
import requests
from config.settings import settings
from PIL import Image

metrics_icon = Image.open("assets/metrics.png")

st.set_page_config(
    page_title="RAG Evaluation",
    page_icon=metrics_icon,
    layout="wide"
)
st.title("RAG Evaluation Dashboard")


# Metrics
try:
    fastapi_url=f"{settings.API_BASE_URL}/metrics/averages"
    resp = requests.get(url=fastapi_url, timeout=10)
    if resp.status_code == 200:
        hist = resp.json()
        st.subheader("Metrics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(":blue[Answer Relevance]",  f"{hist['avg_answer_relevance']:.3f}"  if hist["avg_answer_relevance"]  is not None else "N/A")
        m2.metric(":blue[Context Relevance]", f"{hist['avg_context_relevance']:.3f}" if hist["avg_context_relevance"] is not None else "N/A")
        m3.metric(":blue[Groundedness]",      f"{hist['avg_groundedness']:.3f}"      if hist["avg_groundedness"]      is not None else "N/A")
        m4.metric(":blue[Total Evaluations]", hist["total_evaluations"])
        st.divider()

except requests.exceptions.RequestException:
    st.warning("Could not load historic metrics..")

if "df" not in st.session_state:
    st.session_state.df = None
if "file_loaded" not in st.session_state:
    st.session_state.file_loaded = False
if "scores_df" not in st.session_state:
    st.session_state.scores_df = None

if "rag" not in st.session_state:
    from agents.rag_agent_evaluation import RAG_agent
    st.session_state.rag = RAG_agent()

def invoke_rag(query: str) -> dict:
    rag = st.session_state.rag
    response = asyncio.run(
        rag.rag_agent(query=query, session_id="Session-012i13123123")
    )
    
    context = response.get("context")
    if isinstance(context, list) and len(context) > 0 and isinstance(context[0], list):
        context = [item for sublist in context for item in sublist]

    return {
        "response": response.get("response"),
        "context": context
    }

st.markdown(
        """<style>[data-testid="stSidebarNav"] { display: none; }</style>""",
        unsafe_allow_html=True
    )

with st.sidebar:
    s_col1, s_col2, c3 = st.columns([5, 5, 1])
    with s_col1:
        if st.button("🏠︎Home", key="backtohome", help="Back to Dashboard"):
            st.switch_page("main.py")

file_data = st.file_uploader("Upload RAG Evaluation Data (CSV)", type=["csv"])

if file_data is not None and st.button("Load Data", key="load_data"):
    st.session_state.df = pd.read_csv(file_data)
    st.session_state.file_loaded = True
    st.session_state.scores_df = None       

if st.session_state.file_loaded and st.session_state.df is not None:
    st.subheader("Uploaded Questions")
    st.dataframe(st.session_state.df.head())

    if st.button("Generate RAG Responses", key="generate_rag"):
        questions = st.session_state.df["Questions"].tolist()
        responses = []
        contexts = []
        total = len(questions)
        progress = st.progress(0)
        status_text = st.empty()

        for i, question in enumerate(questions):
            status_text.text(f"Processing question {i + 1} of {total} ({int((i + 1) / total * 100)}% complete)")
            result = invoke_rag(query=question)
            responses.append(result.get("response"))
            contexts.append(result.get("context"))
            progress.progress((i + 1) / total)

        status_text.text(f"All {total} questions processed (100% complete)")
        st.session_state.df["Response"] = responses
        st.session_state.df["Context"]  = contexts
        st.success(" RAG Generation Completed")
        st.dataframe(st.session_state.df.head())

    #Evaluate metrics 
    responses_ready = (
        "Response" in st.session_state.df.columns
        and "Context" in st.session_state.df.columns
    )

    if responses_ready:
        if st.button("Run Evaluation", key="run_eval"):
            with st.spinner("Running Deepeval evaluation..."):
                from utils.rag_metrics import evaluate_dataframe
                scores_df = evaluate_dataframe(st.session_state.df.copy())
                st.session_state.scores_df = scores_df

            st.success(" Evaluation Complete — scores saved to MongoDB")

    if st.session_state.scores_df is not None:
        st.subheader("Evaluation Results")
        st.dataframe(st.session_state.scores_df)

        # Summary metrics
        score_cols = ["Answer Relevance", "Context Relevance", "Groundedness"]
        available  = [c for c in score_cols if c in st.session_state.scores_df.columns]
        if available:
            st.subheader("Average Scores")
            cols = st.columns(len(available))
            for col, metric in zip(cols, available):
                avg = st.session_state.scores_df[metric].mean()
                col.metric(metric, f"{avg:.3f}" if pd.notna(avg) else "N/A")