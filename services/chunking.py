from langchain_text_splitters import TokenTextSplitter

def generate_chunks(docs):
    text_splitter = TokenTextSplitter(
    encoding_name="cl100k_base",
    chunk_size=900, chunk_overlap=250)
    
    docs_chunks = text_splitter.split_text(docs)
    return docs_chunks