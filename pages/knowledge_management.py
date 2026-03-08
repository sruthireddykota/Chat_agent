import streamlit as st 
import requests

API_BASE_URL = "http://fastapi:8001"

def get_documents_api():
    res = requests.get(f"{API_BASE_URL}/documents/get")
    if res.status_code == 200:
        return res.json()
    return []

def delete_document_api(document_id):
    res = requests.delete(f"{API_BASE_URL}/documents/{document_id}")
    if res.status_code == 200:
        return res.json().get("deleted")
    return False



st.set_page_config(
    page_title="Knowledge Management",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True
    )


with st.sidebar:
    s_col1, s_col2, c3 = st.columns([5, 5, 1])
    with s_col1:
        if st.button("🏠︎Home", key="backtohome", help="Back to Dashboard"):
            st.switch_page("main.py")
    with s_col2:
        if st.button("🔍Docling", key="nav_to_docling", help="Navigate to Docling"):
            st.switch_page("pages/docling_parser.py")


def document_delete(document_id):
    from services.qdrant_store import Qdrantservice
    try:
        result = delete_document_api(document_id)

        if result:
            response = Qdrantservice().delete_vectors(
                document_id=document_id,
                collection="Documents"
            )

            if response == "completed":
                return True
    except Exception:
        return False
    

st.title("Document Center",text_alignment="center")


with st.container(border=True,horizontal_alignment="center",vertical_alignment="top",
                  height=500,width=1000):
    
    documents_list = get_documents_api()
    col1,col2,col3,col4,col5,col6=st.columns([2,8,3,4,3,2])
    with col1:
        st.write(':blue[S No]')
    with col2:
        st.write(":blue[Document Name]")
    with col3:
        st.write(":blue[File Type]")
    with col5:
        st.write(":blue[Uploaded by]")
    with col4:
        st.write(":blue[Tags]")
    with col6:
        st.write(":blue[Buttons]")
    
        
    for idx,document in enumerate(documents_list):
        col1,col2,col3,col4,col5,col6=st.columns([2,8,3,4,3,2])
        with col1:
            st.write(str(idx+1))
        with col2:
            st.write(document.get("document_name"))
        with col3:
            file_type=document.get("document_type")
            docx_types=["docx","word","vnd.openxmlformats-officedocument.wordprocessingml.document"]
            if file_type == "pdf":
                st.write(f"{file_type} 📕")
            elif file_type in docx_types:
                if file_type == "vnd.openxmlformats-officedocument.wordprocessingml.document":
                    file_type="docx"
                st.write(f"{file_type} 📘")
            else :
                st.write(f"{file_type} 📄")
        with col5:
            st.write(document.get("uploaded_by"))
        with col4:
            st.write(document.get("tags"))
        with col6:
            document_id=document.get("document_id")
            if st.button("❌",key=f"id_{document_id}"):
                response=document_delete(document_id=document_id)
                
                if response:
                    st.success("Document deleted successfully")
                    st.rerun()
                    
            
        
   