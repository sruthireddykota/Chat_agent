import streamlit as st
import requests
import json

st.set_page_config(
    page_title="Docling with Azure Vision",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Docling Document Processor with Azure Vision")
st.markdown("Process documents with AI-powered image descriptions using Azure Vision")

# Sidebar - Azure Configuration
with st.sidebar:
    st.header("🔐 Azure Vision Configuration")
    
    use_azure_vision = st.checkbox("Enable Picture Description", value=False)
    
    if use_azure_vision:
        st.info("📝 Configure your Azure Vision/OpenAI credentials below")
        
        provider = st.selectbox(
            "Provider",
            ["azure", "openai", "anthropic"],
            index=0
        )
        
        if provider == "azure":
            azure_endpoint = st.text_input(
                "Azure Endpoint",
                placeholder="https://your-resource.cognitiveservices.azure.com/",
                help="Your Azure Computer Vision or OpenAI endpoint"
            )
            
            azure_api_key = st.text_input(
                "Azure API Key",
                type="password",
                help="Found in Azure Portal > Keys and Endpoint"
            )
            
            azure_deployment = st.text_input(
                "Deployment Name",
                placeholder="gpt-4-vision",
                help="Your Azure OpenAI deployment name"
            )
            
            azure_api_version = st.text_input(
                "API Version",
                value="2024-02-01",
                help="Azure API version"
            )
        
        elif provider == "openai":
            openai_api_key = st.text_input(
                "OpenAI API Key",
                type="password"
            )
            openai_model = st.text_input(
                "Model",
                value="gpt-4-vision-preview"
            )
        
        area_threshold = st.slider(
            "Area Threshold",
            min_value=0.01,
            max_value=0.20,
            value=0.05,
            step=0.01,
            help="Minimum percentage of page area for image to be processed (5% = 0.05)"
        )
        
        st.markdown("---")
    
    st.header("⚙️ General Settings")
    
    docling_url = st.text_input(
        "Docling API URL",
        value="http://localhost:5001"
    )
    
    output_format = st.selectbox(
        "Output Format",
        ["md", "json", "html", "text"],
        index=0
    )
    
    st.markdown("---")
    st.header("📊 Processing Options")
    
    do_ocr = st.checkbox("Enable OCR", value=True)
    do_table_structure = st.checkbox("Extract Tables", value=True)
    do_formula_enrichment = st.checkbox("Extract Formulas (LaTeX)", value=False)
    do_chart_extraction = st.checkbox("Extract Chart Data", value=False)

# Main content
tab1, tab2 = st.tabs(["📁 File Upload", "🔗 URL Processing"])

# Helper function to build Azure config
def get_vision_config():
    if not use_azure_vision:
        return None
    
    if provider == "azure":
        if not all([azure_endpoint, azure_api_key, azure_deployment]):
            st.error("❌ Please fill in all Azure Vision fields")
            return None
        
        # Azure OpenAI format for picture_description_api
        return {
            "url": f"{azure_endpoint}/openai/deployments/{azure_deployment}/chat/completions?api-version={azure_api_version}",
            "headers": {
                "api-key": azure_api_key,
                "Content-Type": "application/json"
            },
            "params": {
                "model": azure_deployment,
                "max_tokens": 300
            },
            "prompt": "Describe this image in detail.",
            "timeout": 60,
            "concurrency": 1
        }
    
    elif provider == "openai":
        if not openai_api_key:
            st.error("❌ Please provide OpenAI API key")
            return None
        
        # OpenAI format
        return {
            "url": "https://api.openai.com/v1/chat/completions",
            "headers": {
                "Authorization": f"Bearer {openai_api_key}",
                "Content-Type": "application/json"
            },
            "params": {
                "model": openai_model,
                "max_tokens": 300
            },
            "prompt": "Describe this image in detail.",
            "timeout": 60,
            "concurrency": 1
        }
    
    return None

# Tab 1: File Upload
with tab1:
    st.header("Upload Documents")
    
    uploaded_files = st.file_uploader(
        "Choose files",
        accept_multiple_files=True,
        type=['pdf', 'docx', 'pptx', 'png', 'jpg', 'jpeg']
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) selected")
        
        if st.button("🚀 Process Documents", type="primary", key="process_files"):
            vision_config = get_vision_config()
            
            # Only proceed if Azure config is valid (when enabled)
            if use_azure_vision and vision_config is None:
                st.stop()
            
            with st.spinner("Processing documents..."):
                try:
                    # Prepare files
                    files = []
                    for uploaded_file in uploaded_files:
                        files.append(
                            ('files', (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type))
                        )
                    
                    # Build form data
                    data = {
                        'to_formats': [output_format],
                        'do_ocr': str(do_ocr).lower(),
                        'do_table_structure': str(do_table_structure).lower(),
                        'do_formula_enrichment': str(do_formula_enrichment).lower(),
                        'do_chart_extraction': str(do_chart_extraction).lower(),
                        'pdf_backend': 'dlparse_v4',
                        'include_images': 'true',
                        'target_type': 'inbody'
                    }
                    
                    # Add Azure Vision config if enabled
                    if use_azure_vision and vision_config:
                        data['do_picture_description'] = 'true'
                        data['picture_description_area_threshold'] = str(area_threshold)
                        data['picture_description_api'] = json.dumps(vision_config)
                    
                    # Make API request
                    response = requests.post(
                        f"{docling_url}/v1/convert/file",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("✅ Processing completed!")
                        
                        # Metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Status", result.get('status', 'N/A'))
                        with col2:
                            st.metric("Processing Time", f"{result.get('processing_time', 0):.2f}s")
                        with col3:
                            error_count = len(result.get('errors', []))
                            st.metric("Errors", error_count)
                        
                        # Display document content
                        if 'document' in result:
                            doc = result['document']
                            
                            # Show content based on format
                            if output_format == 'md' and doc.get('md_content'):
                                st.subheader("📝 Markdown Output")
                                
                                # Highlight if picture descriptions were added
                                if use_azure_vision:
                                    st.info("💡 Image descriptions from Azure Vision are embedded in the markdown")
                                
                                st.markdown(doc['md_content'])
                                
                                st.download_button(
                                    "⬇️ Download Markdown",
                                    doc['md_content'],
                                    file_name="output.md",
                                    mime="text/markdown"
                                )
                            
                            elif output_format == 'json' and doc.get('json_content'):
                                st.subheader("🔧 JSON Output")
                                st.json(doc['json_content'])
                                
                                st.download_button(
                                    "⬇️ Download JSON",
                                    json.dumps(doc['json_content'], indent=2),
                                    file_name="output.json",
                                    mime="application/json"
                                )
                            
                            elif output_format == 'html' and doc.get('html_content'):
                                st.subheader("🌐 HTML Output")
                                st.code(doc['html_content'], language='html')
                                
                                st.download_button(
                                    "⬇️ Download HTML",
                                    doc['html_content'],
                                    file_name="output.html",
                                    mime="text/html"
                                )
                            
                            elif output_format == 'text' and doc.get('text_content'):
                                st.subheader("📄 Text Output")
                                st.text(doc['text_content'])
                                
                                st.download_button(
                                    "⬇️ Download Text",
                                    doc['text_content'],
                                    file_name="output.txt",
                                    mime="text/plain"
                                )
                        
                        # Show errors
                        if result.get('errors'):
                            with st.expander("⚠️ Warnings/Errors"):
                                for error in result['errors']:
                                    st.warning(error)
                        
                        # Show detailed timings
                        if result.get('timings'):
                            with st.expander("⏱️ Processing Timings"):
                                st.json(result['timings'])
                    
                    else:
                        st.error(f"❌ Error {response.status_code}")
                        st.code(response.text)
                
                except Exception as e:
                    st.error(f"❌ Exception: {str(e)}")
                    st.exception(e)

# Tab 2: URL Processing
with tab2:
    st.header("Process from URL")
    
    url_input = st.text_area(
        "Document URLs (one per line)",
        placeholder="https://example.com/document.pdf\nhttps://example.com/report.docx",
        height=100
    )
    
    if url_input:
        urls = [url.strip() for url in url_input.split('\n') if url.strip()]
        st.success(f"✅ {len(urls)} URL(s) provided")
        
        if st.button("🚀 Process URLs", type="primary", key="process_urls"):
            vision_config = get_vision_config()
            
            if use_azure_vision and vision_config is None:
                st.stop()
            
            with st.spinner("Processing documents from URLs..."):
                try:
                    # Build options
                    options = {
                        "to_formats": [output_format],
                        "do_ocr": do_ocr,
                        "do_table_structure": do_table_structure,
                        "do_formula_enrichment": do_formula_enrichment,
                        "do_chart_extraction": do_chart_extraction,
                        "pdf_backend": "dlparse_v4",
                        "include_images": True
                    }
                    
                    # Add Azure Vision if enabled
                    if use_azure_vision and vision_config:
                        options["do_picture_description"] = True
                        options["picture_description_area_threshold"] = area_threshold
                        options["picture_description_api"] = vision_config
                    
                    # Build payload
                    payload = {
                        "options": options,
                        "sources": [{"kind": "url", "url": url} for url in urls],
                        "target": {"kind": "inbody"}
                    }
                    
                    # Make request
                    response = requests.post(
                        f"{docling_url}/v1/convert/source",
                        json=payload,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("✅ Processing completed!")
                        
                        # Display results (same as file upload)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Status", result.get('status', 'N/A'))
                        with col2:
                            st.metric("Processing Time", f"{result.get('processing_time', 0):.2f}s")
                        
                        if 'document' in result and result['document'].get('md_content'):
                            st.subheader("📝 Output")
                            
                            if use_azure_vision:
                                st.info("💡 Image descriptions from Azure Vision are embedded")
                            
                            st.markdown(result['document']['md_content'])
                            
                            st.download_button(
                                "⬇️ Download",
                                result['document']['md_content'],
                                file_name="output.md"
                            )
                    
                    else:
                        st.error(f"❌ Error {response.status_code}")
                        st.code(response.text)
                
                except Exception as e:
                    st.error(f"❌ Exception: {str(e)}")
                    st.exception(e)

# Footer with instructions
st.markdown("---")
with st.expander("📖 How to Use Azure Vision"):
    st.markdown("""
    ### Setting up Azure Vision
    
    1. **Create Azure Resource:**
       - Go to [Azure Portal](https://portal.azure.com)
       - Create "Azure OpenAI" or "Computer Vision" resource
    
    2. **Get Credentials:**
       - Navigate to your resource
       - Go to "Keys and Endpoint"
       - Copy:
         - Endpoint URL
         - API Key
         - Deployment name (for Azure OpenAI)
    
    3. **Configure in Sidebar:**
       - Enable "Picture Description"
       - Select "azure" as provider
       - Paste your credentials
       - Adjust area threshold (0.05 = 5% of page)
    
    4. **Process Documents:**
       - Upload files or provide URLs
       - Images in your documents will be described by Azure Vision
       - Descriptions will be embedded in the output
    
    ### Area Threshold
    
    - **0.05 (5%)**: Process images that are at least 5% of the page
    - **0.10 (10%)**: Only process larger images (faster, cheaper)
    - **0.01 (1%)**: Process even small images (slower, more expensive)
    
    ### Cost Considerations
    
    - Each image processed = 1 API call to Azure
    - Monitor your Azure usage
    - Use higher thresholds to reduce costs
    """)

st.markdown("---")
st.caption("💡 Tip: Start with a small document to test your Azure configuration before processing large batches")