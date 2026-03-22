from qdrant_client import QdrantClient
from config.settings import settings

class Qdrantservice:
    def __init__(self, host=settings.QDRANT_HOST, port=settings.QDRANT_PORT):
        self.client = QdrantClient(host=host, port=port)
        
    def verify_collection(self,collection_name):
        collections_list=self.client.get_collections()
        for collection in collections_list.collections:
            if collection.name == collection_name:
                return True
            
        else:
            return False
    
    def retrive_documents(self,collection_name:str,embeddings:list,limit:int=6)->list:
        results=self.client.query_points(
            collection_name=collection_name,
            query=embeddings,
            limit=limit
        )
        final_result=[]
        for data in results.points:
            score=data.score
            payload=data.payload
            document_name=payload.get("document_name")
            chunk_id=payload.get("chunk_id")
            content=payload.get("chunk_content")
            chunk_content={
                "document_name":document_name,
                "chunk_id":chunk_id,
                "chunk_content":content,
                "score":score
            }
            final_result.append(chunk_content)
        return final_result
            
    
    