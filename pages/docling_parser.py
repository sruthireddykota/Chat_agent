import streamlit as st

import json
import requests
import uuid
from datetime import datetime
import requests
from config.settings import settings
from PIL import Image

parser_icon=Image.open("assets/parsing.png")

API_BASE_URL = settings.API_BASE_URL

def store_document_api(document_data):
    url = f"{API_BASE_URL}/documents/store"
    res = requests.post(url,json=document_data)
    if res.status_code == 200:
        return res.json()
    return None


st.set_page_config(
    page_title="Document Parser",
    page_icon=parser_icon,
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

st.title("Document Parser",text_alignment='center')

if "result_generated" not in st.session_state:
    st.session_state.result_generated=False

if "chunk_result" not in st.session_state:
    st.session_state.chunk_result=None
    
if "embedding_result" not in st.session_state:
    st.session_state.embedding_result=None
    
if "docling_result" not in st.session_state:
    st.session_state.docling_result=None
    
if "file_data" not in st.session_state:
    st.session_state.file_data=None

if "active_tab" not in st.session_state:
    st.session_state.active_tab= None
    

def clear_session_state():
    st.session_state.docling_result=None
    st.session_state.chunk_result=None
    st.session_state.result_generated=False
    st.session_state.embedding_result=None
    st.session_state.file_data=None
            
    
def document_pipeline(parse_result,tab,file_data=None):
    if parse_result is not None:
        with st.expander(f'filename: :blue[{file_data.get("document_name")}]'):
            st.markdown(f'content: {parse_result}')
            
        chunk_button=st.button(":green[Generate Chunks]",key=f"chunk_generation_{tab}")
        
        if chunk_button:
            from services.chunking import generate_chunks
            chunks=generate_chunks(parse_result)
            if chunks:
                st.session_state.chunk_result=chunks
        if st.session_state.chunk_result is not None:
            
            with st.expander("View Chunks"):
                for idx,chunk in enumerate(st.session_state.chunk_result):
                    with st.expander(f'Chunk :{idx}'):
                        st.text(chunk)
        
            embedding_button=st.button(":green[Generate Embeddings]",key=f"Embedding_generation_{tab}")
            
            if embedding_button:
                from services.embeddings import generate_embeddings
                embeddings=generate_embeddings(st.session_state.chunk_result)
                st.session_state.embedding_result=embeddings
            
        if st.session_state.embedding_result is not None:
            with st.expander("View Embeddings Count"):
                st.write(len(st.session_state.embedding_result))
        
            store_embeddings=st.button(":green[Store Embeddings]",key=f"Store_embeddings_{tab}")
            
            if store_embeddings:
                from services.qdrant_store import Qdrantservice
                service=Qdrantservice()
                collection=service.verify_collection("Documents")
                if collection:
                    chunk_data={
                        "chunks": st.session_state.chunk_result,
                        "document_name":file_data.get("document_name"),
                        "document_id":file_data.get("document_id"),
                    }
                    success,message=service.store_embeddings("Documents",st.session_state.embedding_result,chunk_data)
                    if success:
                        
                        document_data={
                            "document_name":file_data.get("document_name"),
                            "document_id":file_data.get("document_id"),
                            "document_type":file_data.get("document_type"),
                            "timestamp":datetime.utcnow().isoformat(),
                            "chunk_count": len(st.session_state.chunk_result),
                            "uploaded_by":file_data.get("uploaded_by"),
                            "tags":file_data.get("tags")
                        }
                        response=store_document_api(document_data=document_data)
                        if response:
                            st.success(f"Payload Successfully stored in vector Database, {message}")
                            
def get_vision_config():
    from dotenv import load_dotenv
    import os
    load_dotenv()
    end_point=os.getenv("VISION_END_POINT")
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
    deployment_name=os.getenv("VISION_DEPLOYMENT_NAME")

    api_config={
        "url":end_point,
        "concurrency":1,
        "headers":{
            "api-key":api_key,
            "Content-Type":"application/json"
        },
        "params":{
            "model":deployment_name
        },
        "timeout": 600,
        "prompt":"Describe this image in a few sentences"

    }
    return api_config

with st.sidebar:
    
    s_col1, s_col2, c3 = st.columns([5, 1, 1])
    with s_col1:
        if st.button("📚Knowledge Management", key="nav_to_Km", help="Navigate to Knowledge Management"):
            st.switch_page("pages/knowledge_management.py")
            
    st.title("⚙️ General Settings")
    
    output_format=st.selectbox("Output format",
                               ("md","json","html","text"),index=0,key="format_md")
    
    st.markdown("---")
    
    do_ocr=st.checkbox("Enable OCR",value=0,key="ocr_")
    
    do_table_structure=st.checkbox("Enable Table Extraction",value=1,key="table_structure")
    do_picture_description=st.checkbox("Enable Picture Description",value=1,key="picture_description")
    do_code_enrichment=st.checkbox("Enable Code Enrichment",value=0,key="code_enrichment")
    do_formula_enrichment=st.checkbox("Enable Formula Enrichment",value=0,key="formula_enrichment")
    images_scale=st.slider("Image Scale",min_value=1,max_value=3,value=2,step=1,key="images_scale")
    table_mode=st.selectbox("Table Extraction Mode",("Fast","Accurate"),index=0,key="table_mode")
    

tab1,tab2=st.tabs(["File Uploader","Url Processing"])

with tab1:
    st.subheader("Upload Documents",text_alignment="center")
    
    uploaded_file=st.file_uploader("upload file",type=["pdf","docx","xlsx","csv","jpeg","png"])
    
    if uploaded_file is None and st.session_state.active_tab=='file':
        
        clear_session_state()
    if uploaded_file is not None:
        col1,col2=st.columns(2)
        with col1:
            process_button=st.button(":green[Process Document]",key="process_button",on_click=clear_session_state)
            
            if process_button:
                st.session_state.active_tab='file'
                with st.spinner(text="Processing document...."):
                    try:
                        files=[]
                        file_type=uploaded_file.type.split('/')[1]
                        st.session_state.file_data={
                            "document_name":uploaded_file.name,
                            "document_type":file_type,
                            "document_id":str(uuid.uuid4()),
                            "uploaded_by":"Admin",
                            "tags":None
                        }
                        files.append(('files',(uploaded_file.name,uploaded_file.getvalue(),uploaded_file.type)))
                        
                        data={
                            "to_formats":[output_format],
                            "do_ocr":str(do_ocr).lower(),
                            "do_table_structure": str(do_table_structure).lower(),
                            "do_picture_description": str(do_picture_description).lower(),
                            "do_code_enrichment": str(do_code_enrichment).lower(),
                            "do_formula_enrichment": str(do_formula_enrichment).lower(),
                            "images_scale": str(images_scale),
                            "table_mode": table_mode.lower(),
                            "image_export_mode": "referenced",
                            "pipeline_options": json.dumps({
                                "enable_remote_services": True
                            }),
                        }
                        
                        if do_picture_description:
                            data["picture_description_api"]=json.dumps(get_vision_config())
                        
                        response= requests.post(
                            url="http://docling-serve:5001/v1/convert/file",
                            data=data,
                            files=files,
                            timeout=3600,
                        )
                        
                        if response.status_code==200:
                            result=response.json()
                            st.session_state.docling_result={
                                "document":result.get("document"),
                                "status":result.get("status"),
                                "processing_time":result.get("processing_time"),
                                "errors":result.get("errors"),
                                "document_data":st.session_state.file_data
                            }
                            st.session_state.result_generated=True
                            
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        with col2:
            st.button(":red[Clear Documents]",key="clear session states",on_click=clear_session_state)
                    
    if st.session_state.result_generated and st.session_state.active_tab=='file':
        col1,col2,col3=st.columns(3)
        with col1:
            st.badge("Status",color="blue")
            st.markdown(st.session_state.docling_result.get("status"))
        with col2:
            st.badge("Processing Time",color="orange")
            st.markdown(f'{st.session_state.docling_result.get("processing_time",0):.2f}s')
        with col3: 
            st.badge("Errors",color="red")
            st.markdown(st.session_state.docling_result.get("errors",[]))
        
        if st.session_state.docling_result.get("document")and output_format=="md":
            doc=st.session_state.docling_result.get("document")
            parse_result=doc.get("md_content",None)
            file_data=st.session_state.docling_result.get("document_data")
            document_pipeline(parse_result=parse_result,tab="doc",file_data=file_data)
            
        elif st.session_state.docling_result.get("document")and output_format=="text":
            doc=st.session_state.docling_result.get("document")
            parse_result=doc.get("text_content",None)
            file_data=st.session_state.docling_result.get("document_data")
            document_pipeline(parse_result=parse_result,tab="doc",file_data=file_data)
        
        elif st.session_state.docling_result.get("document")and output_format=="html":
            doc=st.session_state.docling_result.get("document")
            with st.expander(f'filename: :blue[{doc.get("filename")}]'):
                st.code(doc.get("html_content"),language="html")
            
        elif st.session_state.docling_result.get("document")and output_format=="json":
            doc=st.session_state.docling_result.get("document")
            with st.expander(f'filename: :blue[{doc.get("filename")}]s'):
                st.json(doc.get("json_content"))
   
with tab2:
    
    st.subheader("Process URL",text_alignment="center")
    uploaded_url=st.text_area(
        "Document URLs (one per line)",
        placeholder="https://example.com/document.pdf\nhttps://example.com/report.docx",
        height=100
    )
    
    if not uploaded_url and st.session_state.active_tab == 'url':
        clear_session_state()
        
    if uploaded_url is not None:
        urls = [url.strip() for url in uploaded_url.split('\n') if url.strip()]
        col1,col2=st.columns(2)
        with col1:
            process_button=st.button(":green[Process URL]",key="url_process_button",on_click=clear_session_state)
            if process_button:
                st.session_state.active_tab='url'
                with st.spinner(text="Processing url...."): 
                    try:
                        
                        data={
                            "to_formats":[output_format],
                            "do_ocr": do_ocr,
                            "do_table_structure": do_table_structure,
                            "do_picture_description": do_picture_description,
                            "do_code_enrichment": do_code_enrichment,
                            "do_formula_enrichment": do_formula_enrichment,
                            "images_scale": images_scale,
                            "table_mode": table_mode.lower(),
                            "image_export_mode": "referenced",
                            "pipeline_options": {
                                "enable_remote_services": True
                            },
                        }
                        
                        if do_picture_description:
                            data["picture_description_api"]= get_vision_config()
                            
                        payload = {
                            "options": data,
                            "sources": [{"kind": "http", 
                                        "url": url} for url in urls],
                            "target": {"kind": "inbody"}
                        }
                        
                        response= requests.post(
                            url="http://docling-serve:5001/v1/convert/source",
                            json=payload,
                            headers={'Content-Type': 'application/json'},
                            timeout=3600
                        )
                        if response.status_code==200:
                            result=response.json()
                            document_name=result.get("document").get("filename")
                            
                            st.session_state.file_data={
                                "document_name":document_name,
                                "document_type":document_name.split(".")[1],
                                "document_id":str(uuid.uuid4()),
                                "uploaded_by":"Admin",
                                "tags":None
                                }
                            
                            st.session_state.docling_result={
                                "document":result.get("document"),
                                "status":result.get("status"),
                                "processing_time":result.get("processing_time"),
                                "errors":result.get("errors"),
                                "document_data":st.session_state.file_data
                            }
                            st.session_state.result_generated=True
                        else:
                            st.error(f"Error {response.status_code}")
                            st.code(response.text)    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        with col2:
            st.button(":red[Clear Documents]",key="document_clear2",on_click=clear_session_state)
                    
    if st.session_state.result_generated and st.session_state.active_tab=='url':
        col1,col2,col3=st.columns(3)
        with col1:
            st.badge("Status",color="blue")
            st.markdown(st.session_state.docling_result.get("status"))
        with col2:
            st.badge("Processing Time",color="orange")
            st.markdown(f'{st.session_state.docling_result.get("processing_time",0):.2f}s')
        with col3:
            st.badge("Errors",color="red")
            st.markdown(st.session_state.docling_result.get("errors",[]))
        
        if st.session_state.docling_result.get("document")and output_format=="md":
            doc=st.session_state.docling_result.get("document")
            parse_result=doc.get("md_content",None)
            file_data=st.session_state.docling_result.get("document_data")
            document_pipeline(parse_result=parse_result,tab="url",file_data=file_data)
            
        elif st.session_state.docling_result.get("document")and output_format=="text":
            doc=st.session_state.docling_result.get("document")
            parse_result=doc.get("md_content",None)
            file_data=st.session_state.docling_result.get("document_data")
            document_pipeline(parse_result=parse_result,tab="url",file_data=file_data)
        
        elif st.session_state.docling_result.get("document")and output_format=="html":
            doc=st.session_state.docling_result.get("document")
            with st.expander(f'filename: :blue[{doc.get("filename")}]'):
                st.code(doc.get("html_content"),language="html")
            
        elif st.session_state.docling_result.get("document")and output_format=="json":
            doc=st.session_state.docling_result.get("document")
            with st.expander(f'filename: :blue[{doc.get("filename")}]s'):
                st.json(doc.get("json_content"))
                    