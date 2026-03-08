from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance,PointStruct,Filter,FieldCondition,MatchValue
import uuid
import os
class Qdrantservice:
    
    def __init__(self, host=os.getenv("QDRANT_HOST"), port=os.getenv("QDRANT_PORT")):
        self.client = QdrantClient(host=host, port=port)
    
    def create_collection(self,collection):
        self.client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE
        )
        )
    def verify_collection(self,collection):
        collections_list=self.client.get_collections()
        for coll in collections_list.collections:
            if collection == coll.name:
                return True
        else:
            self.create_collection(collection)
            return True
        
    def store_embeddings(self,collection,embeddings,chunks_data):
        points=[]
        chunks=chunks_data.get("chunks")
        for i ,vector in enumerate(embeddings):

            payload={
            
                "document_id":chunks_data.get("document_id"),
                "document_name":chunks_data.get("document_name"),
                "chunk_id":i,
                "chunk_content":chunks[i]
             
            }
            
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=payload
                )
            )
            
        self.client.upsert(
            collection_name=collection,
            points=points
            )
        return True,f"{len(points)} embeddings stored "
    
    def delete_vectors(self,document_id,collection):
        response=self.client.delete(
            collection_name=collection,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
        return response.status
        
        





