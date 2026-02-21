import streamlit as st
import json
import requests
from typing import List, Dict, Any

st.set_page_config(
    page_title="Document Parser",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("Document Parser")

def get_vision_config():
    end_point = st.secrets["VISION_END_PONIT"]
    api_key = st.secrets["AZURE_OPENAI_API_KEY"]
    deployment_name = st.secrets["VISION_DEPLOYMENT_NAME"]
    
    api_config = {
        "url": end_point,
        "concurrency": 1,
        "headers": {
            "api-key": api_key,
            "Content-Type": "application/json"
        },
        "params": {
            "model": deployment_name
        },
        "timeout": 300,
        "prompt": "Describe this image in a few sentences"
    }
    return api_config

def get_embedding_config():
    """Get embedding API configuration from secrets"""
    return {
        "endpoint": st.secrets.get("EMBEDDING_ENDPOINT", "http://localhost:5001/v1/embeddings"),
        "api_key": st.secrets.get("EMBEDDING_API_KEY", ""),
        "model": st.secrets.get("EMBEDDING_MODEL", "text-embedding-ada-002")
    }

def generate_embeddings_batch(chunks: List[Dict[str, Any]], batch_size: int = 10) -> List[Dict[str, Any]]:
    """Generate embeddings for chunks in batches"""
    embedding_config = get_embedding_config()
    results = []
    
    total_chunks = len(chunks)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(0, total_chunks, batch_size):
        batch = chunks[i:i + batch_size]
        batch_texts = [chunk.get("text", "") for chunk in batch]
        
        status_text.text(f"Processing batch {i//batch_size + 1} of {(total_chunks + batch_size - 1)//batch_size}...")
        
        try:
            # Prepare payload for embedding API
            payload = {
                "model": embedding_config["model"],
                "input": batch_texts
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            if embedding_config["api_key"]:
                headers["Authorization"] = f"Bearer {embedding_config['api_key']}"
            
            response = requests.post(
                embedding_config["endpoint"],
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                embeddings_data = response.json()
                
                # Combine chunks with their embeddings
                for j, chunk in enumerate(batch):
                    chunk_with_embedding = chunk.copy()
                    chunk_with_embedding["embedding"] = embeddings_data.get("data", [])[j].get("embedding", [])
                    chunk_with_embedding["embedding_model"] = embedding_config["model"]
                    results.append(chunk_with_embedding)
            else:
                st.error(f"Batch {i//batch_size + 1} failed: {response.status_code} - {response.text}")
                # Add chunks without embeddings
                results.extend(batch)
                
        except Exception as e:
            st.error(f"Error processing batch {i//batch_size + 1}: {str(e)}")
            results.extend(batch)
        
        # Update progress
        progress_bar.progress((i + batch_size) / total_chunks)
    
    progress_bar.empty()
    status_text.empty()
    
    return results

def display_chunk_details(chunk: Dict[str, Any], chunk_idx: int):
    chunk_title = f"Chunk {chunk_idx + 1}"
    if chunk.get("headings"):
        chunk_title += f" - {chunk['headings'][0][:50]}..."
    
    with st.expander(chunk_title):
        col1, col2, col3,col4 = st.columns(4)
        
        with col1:
            st.metric("Chunk Index", chunk.get("chunk_index", chunk_idx))
        
        with col2:
            pages = chunk.get("page_numbers", [])
            if pages:
                st.metric("Pages", f"{min(pages)}-{max(pages)}" if len(pages) > 1 else str(pages[0]))
            else:
                st.metric("Pages", "N/A")
        
        with col3:
            st.metric("Tokens", chunk.get("num_tokens", 0))
            
        with col4:
            if chunk.get("headings"):
                st.metric("Headings", len(chunk["headings"]))
        
        
        # headings
        if chunk.get("headings"):
            st.markdown("Headings:")
            for heading in chunk["headings"]:
                st.markdown(f"- {heading}")
        
        # captions
        if chunk.get("captions"):
            st.markdown("Captions:")
            for caption in chunk["captions"]:
                st.markdown(f"- {caption}")
        
        # text content
        st.markdown("Text Content:")
        st.text_area(
            "Chunk Text",
            value=chunk.get("text", ""),
            height=200,
            key=f"chunk_text_{chunk_idx}",
            label_visibility="collapsed"
        )
        
        # raw text
        if chunk.get("raw_text") and chunk.get("raw_text") != chunk.get("text"):
            with st.expander("View Raw Text"):
                st.text_area(
                    "Raw Text",
                    value=chunk.get("raw_text", ""),
                    height=150,
                    key=f"chunk_raw_{chunk_idx}",
                    label_visibility="collapsed"
                )
        
        # metadata
        if chunk.get("metadata"):
            with st.expander("View Metadata"):
                st.json(chunk["metadata"])

with st.sidebar:
    st.title("⚙️ General Settings")
    
    output_format = st.selectbox("Output format",
                                 ("md", "json", "html", "text"), index=0, key="format_md")
    
    st.markdown("---")
    
    do_ocr = st.checkbox("Enable OCR", value=False, key="ocr_")
    
    do_table_structure = st.checkbox("Enable Table Extraction",
                                     value=True, key="table_structure")
    
    do_picture_description = st.checkbox("Enable Picture Description", 
                                         value=True, key="picture_description")
    
    do_code_enrichment = st.checkbox("Enable Code Enrichment", 
                                     value=False, key="code_enrichment")
    do_formula_enrichment = st.checkbox("Enable Formula Enrichment", 
                                        value=False, key="formula_enrichment")
    
    images_scale = st.slider("Image Scale", min_value=1, max_value=3, value=2, step=1, key="images_scale")
    
    table_mode = st.selectbox("Table Extraction Mode", ("Fast", "Accurate"), index=0, key="table_mode")
    
    st.subheader("Embedding Settings")
    batch_size = st.number_input("Embedding Batch Size", min_value=1, max_value=100, value=10, key="batch_size")

tab1, tab2 = st.tabs(["File Uploader", "URL Processing"])

with tab1:
    st.title("Upload Documents", anchor=False)
    uploaded_file = st.file_uploader("upload file", type=["pdf", "docx", "xlsx", "csv", "jpeg", "png"])
   
    if uploaded_file is not None:
        process_button = st.button("Process Document", key="process_button")
        if process_button:
            with st.spinner(text="Processing document...."):
                try:
                    files = []
                    files.append(('files', (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)))
                    
                    data = {
                        "include_converted_doc": "true",
                        "convert_from_formats": output_format,
                        "convert_do_ocr": str(do_ocr).lower(),
                        "convert_do_table_structure": str(do_table_structure).lower(),
                        "convert_do_picture_description": str(do_picture_description).lower(),
                        "convert_do_code_enrichment": str(do_code_enrichment).lower(),
                        "convert_do_formula_enrichment": str(do_formula_enrichment).lower(),
                        "convert_images_scale": str(images_scale),
                        "convert_table_mode": table_mode.lower(),
                        "convert_image_export_mode": "embedded",
                        "pipeline_options": json.dumps({
                            "enable_remote_services": True
                        }),
                        "chunking_use_markdown_tables": "true",
                        "chunking_max_tokens": 1200,
                    }
                    
                    if do_picture_description:
                        data["convert_picture_description_api"] = json.dumps(get_vision_config())
                    
                    response = requests.post(
                        url="http://localhost:5001/v1/chunk/hybrid/file",
                        data=data,
                        files=files
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.write(result)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.badge("Status")
                            status_result = result.get("documents", [{}])[0]
                            st.markdown(status_result.get("status", "Unknown"))
                        with col2:
                            st.badge("Processing Time")
                            st.markdown(f'{result.get("processing_time", 0):.2f}s')

                        # document content
                        if result.get("documents") and output_format == "md":
                            doc_result = result.get("documents")[0]
                            doc = doc_result.get("content", {})
                            
                            with st.expander(f'Document: :blue[{doc.get("filename", "Unknown")}]'):
                                st.markdown(doc.get("md_content", "No content available"))
                                
                            with st.expander(f'View chunks:blue[{doc.get("filename", "Unknown")}]'):
                                chunks=result.get("chunks")
                                for idx,chunk in enumerate(chunks):
                                    display_chunk_details(chunk=chunk,chunk_idx=idx)
                        
                        elif result.get("documents") and output_format == "text":
                            doc_result = result.get("documents")[0]
                            doc = doc_result.get("content", {})
                            with st.expander(f'Document: :blue[{doc.get("filename", "Unknown")}]'):
                                st.markdown(doc.get("text_content", "No content available"))
                                
                            with st.expander(f'View chunks:blue[{doc.get("filename", "Unknown")}]'):
                                chunks=result.get("chunks")
                                for idx,chunk in enumerate(chunks):
                                    display_chunk_details(chunk=chunk,chunk_index=idx)
                        
                        elif result.get("documents") and output_format == "html":
                            doc_result = result.get("documents")[0]
                            doc = doc_result.get("content", {})
                            with st.expander(f'Document: :blue[{doc.get("filename", "Unknown")}]'):
                                st.code(doc.get("html_content", ""), language="html")
                                
                            with st.expander(f'View chunks:blue[{doc.get("filename", "Unknown")}]'):
                                chunks=result.get("chunks")
                                for idx,chunk in enumerate(chunks):
                                    display_chunk_details(chunk=chunk,chunk_index=idx)
                        
                        elif result.get("documents") and output_format == "json":
                            doc_result = result.get("documents")[0]
                            doc = doc_result.get("content", {})
                            with st.expander(f'Document: :blue[{doc.get("filename", "Unknown")}]'):
                                st.json(doc.get("json_content", {}))
                                
                            with st.expander(f'View chunks:blue[{doc.get("filename", "Unknown")}]'):
                                chunks=result.get("chunks")
                                for idx,chunk in enumerate(chunks):
                                    display_chunk_details(chunk=chunk,chunk_index=idx)
                        
                        st.success("Document processed successfully!")
                            
                    else:
                        st.error(f"Error {response.status_code}")
                        st.code(response.text)
                            
                except Exception as e:
                    st.error(f"Error: {str(e)}")

with tab2:
    st.title("Process URL", anchor=False)
    uploaded_url = st.text_area(
        "Document URLs (one per line)",
        placeholder="https://example.com/document.pdf\nhttps://example.com/report.docx",
        height=100
    )
    
    if uploaded_url:
        urls = [url.strip() for url in uploaded_url.split('\n') if url.strip()]
        process_button = st.button("Process URL", key="url_process_button")
        
        if process_button:
            with st.spinner(text="Processing URL...."):
                try:
                    data = {
                        "to_formats": [str(output_format)],
                        "do_ocr": do_ocr,
                        "do_table_structure": do_table_structure,
                        "do_picture_description": do_picture_description,
                        "do_code_enrichment": do_code_enrichment,
                        "do_formula_enrichment": do_formula_enrichment,
                        "images_scale": images_scale,
                        "table_mode": table_mode.lower(),
                        "image_export_mode": "embedded",
                        "pipeline_options": {
                            "enable_remote_services": True
                        },
                    }
                    chucking_config={
                        "use_markdown_tables": True,
                        "max_tokens":1200,
                        
                        
                    }
                    
                    if do_picture_description:
                        data["picture_description_api"] = get_vision_config()
                        
                    payload = {
                        "convert_options": data,
                        "sources": [{"kind": "http", "url": url} for url in urls],
                        "target": {"kind": "inbody"},
                        "chunking_options":chucking_config,
                        "include_converted_doc": True
                    }
                    
                    response = requests.post(
                        url="http://localhost:5001/v1/chunk/hybrid/source",
                        json=payload,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        col1, col2 = st.columns(2)
                        with col1:
                            st.badge("Status")
                            status_result = result.get("documents", [{}])[0]
                            st.markdown(status_result.get("status", "Unknown"))
                        with col2:
                            st.badge("Processing Time")
                            st.markdown(f'{result.get("processing_time", 0):.2f}s')

                        # document content
                        if result.get("documents") and output_format == "md":
                            doc_result = result.get("documents")[0]
                            doc = doc_result.get("content", {})
                            
                            with st.expander(f'Document: :blue[{doc.get("filename", "Unknown")}]'):
                                st.markdown(doc.get("md_content", "No content available"))
                                
                            with st.expander(f'View chunks:blue[{doc.get("filename", "Unknown")}]'):
                                chunks=result.get("chunks")
                                for idx,chunk in enumerate(chunks):
                                    display_chunk_details(chunk=chunk,chunk_idx=idx)
                        
                        elif result.get("documents") and output_format == "text":
                            doc_result = result.get("documents")[0]
                            doc = doc_result.get("content", {})
                            with st.expander(f'Document: :blue[{doc.get("filename", "Unknown")}]'):
                                st.markdown(doc.get("text_content", "No content available"))
                                
                            with st.expander(f'View chunks:blue[{doc.get("filename", "Unknown")}]'):
                                chunks=result.get("chunks")
                                for idx,chunk in enumerate(chunks):
                                    display_chunk_details(chunk=chunk,chunk_index=idx)
                        
                        elif result.get("documents") and output_format == "html":
                            doc_result = result.get("documents")[0]
                            doc = doc_result.get("content", {})
                            with st.expander(f'Document: :blue[{doc.get("filename", "Unknown")}]'):
                                st.code(doc.get("html_content", ""), language="html")
                                
                            with st.expander(f'View chunks:blue[{doc.get("filename", "Unknown")}]'):
                                chunks=result.get("chunks")
                                for idx,chunk in enumerate(chunks):
                                    display_chunk_details(chunk=chunk,chunk_index=idx)
                        
                        elif result.get("documents") and output_format == "json":
                            doc_result = result.get("documents")[0]
                            doc = doc_result.get("content", {})
                            with st.expander(f'Document: :blue[{doc.get("filename", "Unknown")}]'):
                                st.json(doc.get("json_content", {}))
                                
                            with st.expander(f'View chunks:blue[{doc.get("filename", "Unknown")}]'):
                                chunks=result.get("chunks")
                                for idx,chunk in enumerate(chunks):
                                    display_chunk_details(chunk=chunk,chunk_index=idx)
                        
                        st.success("Document processed successfully!")
                            
                    else:
                        st.error(f"Error {response.status_code}")
                        st.code(response.text)
                            
                except Exception as e:
                    st.error(f"Error: {str(e)}")