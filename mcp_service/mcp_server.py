from fastmcp import FastMCP
import os
import requests
from typing import Optional
from starlette.responses import JSONResponse
import time
import hashlib

mcp = FastMCP("MCP server")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

last_request_time = 0
MIN_REQUEST_INTERVAL = 1.1  # 1.1 seconds to be safe

cache_duration = 300
search_cache = {}

def get_cache_key(query: str, count: int, freshness: Optional[str]) -> str:
    cache_str = f"{query}:{count}:{freshness}"
    return hashlib.md5(cache_str.encode()).hexdigest()

def wait_for_rate_limit():
    global last_request_time
    current_time = time.time()
    time_since_last = current_time - last_request_time
    
    if time_since_last < MIN_REQUEST_INTERVAL:
        sleep_time = MIN_REQUEST_INTERVAL - time_since_last
        print(f"Rate limiting: waiting {sleep_time:.2f}s...")
        time.sleep(sleep_time)
    
    last_request_time = time.time()


@mcp.tool()
def brave_web_search(query: str, count: int = 10,freshness: Optional[str] = None) -> dict:
    """
    Search the web using Brave Search API with rate limiting and caching.
    
    Args:
        query: The search query string
        count: Number of results to return (max 20, default 10)
        freshness: Filter by time - 'pd' (past day), 'pw' (past week), 
                   'pm' (past month), 'py' (past year)
    
    Returns:
        Dictionary containing search results with titles, URLs, and descriptions
    """
    if not BRAVE_API_KEY:
        return {"error": "BRAVE_API_KEY environment variable not set"}
    
    # cache first
    cache_key = get_cache_key(query, count, freshness)
    if cache_key in search_cache:
        cached_result, cached_time = search_cache[cache_key]
        if time.time() - cached_time < cache_duration:
            print(f"Returning cached result for: {query}")
            return {**cached_result, "cached": True}
    
    try:
        # Wait to respect rate limit
        wait_for_rate_limit()
        
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_API_KEY
        }
        
        params = {"q": query}
        
        if count and count != 10:
            params["count"] = min(count, 20)
        
        if freshness in {"pd", "pw", "pm", "py"}:
            params["freshness"] = freshness
                
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
            timeout=60
        )
        
        if response.status_code == 429:
            error_data = response.json()
            meta = error_data.get("error", {}).get("meta", {})
            return {
                "error": "Rate limit exceeded",
                "details": {
                    "plan": meta.get("plan", "Unknown"),
                    "rate_limit": f"{meta.get('rate_limit', 'Unknown')} requests/second",
                    "quota_used": f"{meta.get('quota_current', 0)}/{meta.get('quota_limit', 0)}",
                    "message": "Wait at least 1 second between requests"
                }
            }
        
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        if "web" in data and "results" in data["web"]:
            for result in data["web"]["results"]:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "description": result.get("description", ""),
                    "age": result.get("age", "")
                })
        
        result_data = {
            "query": query,
            "result_count": len(results),
            "results": results,
            "cached": False
        }
        
        search_cache[cache_key] = (result_data, time.time())
        
        return result_data
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP {e.response.status_code}"
        if e.response.text:
            error_msg += f": {e.response.text[:200]}"
        return {"error": error_msg}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}


def embed_search(query,limit):
    from services.query_embeddings import query_embedding
    from services.qdrant_retrevial import Qdrantservice
    embedding=query_embedding(query=query)
    service=Qdrantservice()
    response=service.verify_collection(collection_name="Documents")
    if response:
        results=service.retrive_documents(collection_name="Documents",
                                  embeddings=embedding,
                                  limit=limit)
        return results
    
@mcp.tool()
def rag_retrive(query:str)->dict:
    """
    This tool takes a user query and returns top retrived chunks from the document database

    Args:
        query (str): The query given by the user 

    Returns:
        dict : This returns top Retrived chunk information 
    """
    try:
        response=embed_search(query=query,limit=6)
        final_response=''
        chunks=[]
        for chunk in response:
            document_name=chunk.get("document_name")
            chunk_id=chunk.get("chunk_id")
            chunk_content=chunk.get("chunk_content")
            score=chunk.get("score")
            chunks.append(chunk_content)#for evaluation metrics
            chunk_data=f"Document name: {document_name}, Chunk_id: {chunk_id}, Score: {score}, Chunk_content: {chunk_content}\n\n"
            final_response +=chunk_data
        return {
            'final_response':final_response,#rag agent
            'chunks': chunks #evaluations metrics in list format
        }
    except Exception as e:
        return {                           
            "final_response": f"No Documents Found, try again. Error: {e}",
            "chunks": []
        }

@mcp.tool()
def get_chat_history(session_id:str)->str:
    """To get the chat history 

    Args:
        session_id (str): Current user session id 

    Returns:
        str: role of the user and content 
    """
    from services.chat_history_retrieval import MongoStore
    try:
        response=MongoStore().get_chat_history(session_id=session_id,limit=6)
        return response
    except Exception as e:
        return f"No Chat History Found,error:{e}"
    
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({
        "status": "Healthy",
        "service": "mcp-server",
        "cache_size": len(search_cache)
    })


if __name__ == "__main__":
    mcp.run(transport='streamable-http')