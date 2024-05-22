from icecream import ic

from langchain_community.vectorstores import Qdrant

from qdrant_client import QdrantClient
from qdrant_client.http import models

def get_qdrant_vector_store(
        host: str,
        port: int,
        embeddings,
        collection_name: str,
):
    client = QdrantClient(host=host, port=port)
    # Check if the collection exists
    collection_exists = client.collection_exists(collection_name=collection_name)
    # If the collection does not exist, create it with the specified configuration
    if not collection_exists:
        ic(f"creating collection {collection_name}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
        )

    db = Qdrant(
        client=client, collection_name=collection_name,
        embeddings=embeddings,
    )
    return db