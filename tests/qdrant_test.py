from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance,PointStruct,Filter,FieldCondition,MatchValue
import uuid

class Qdrantservice:
    
    def __init__(self, host="localhost", port=6333):
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
                "chunks":chunks[i],
                "chunk_id":i,
                "document_name":chunks_data.get("document_name")
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
        v=self.client.delete(
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
        return v.status
        
    def retrive_documents(self,collection_name:str,embeddings:list,limit:int=6)->list:
        results=self.client.query_points(
            collection_name=collection_name,
            query=embeddings,
            limit=limit
        )
        return results
        

service=Qdrantservice()
# print(service.verify_collection("Documents"))
# print(service.delete_vectors("69d1b673-fcea-4926-9c63-0a3c08ad1385","Documents"))

from openai import AzureOpenAI
import os
from dotenv import load_dotenv
load_dotenv()

def get_embedding_client():
    client=AzureOpenAI(
        api_key=os.getenv("EMBEDDING_API_KEY"),
        azure_endpoint=os.getenv("EMBEDDING_ENDPOINT"),
        api_version="2024-02-15-preview"
    )
    return client

client=get_embedding_client()

def query_embedding(query):
    response=client.embeddings.create(
        model=os.getenv("EMBEDDING_MODEL"),
        input=query
    )
    return response.data[0].embedding

embed=query_embedding("Hello")
r=service.retrive_documents("Documents",embed,2)
for r in r.points:
    score=r.score
    payload=r.payload 
    
    print(r)




