import os
import ollama
from pinecone import Pinecone
from crawl4ai.models import CrawlResult
from langchain.text_splitter import RecursiveCharacterTextSplitter

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

def generate_embedding_from_text(text: str) -> list[float]:
    response = ollama.embed(model="nomic-embed-text", input=text)
    embedding = response["embeddings"]
    return embedding

def add_text_to_index(results: list[CrawlResult]):
    for result in results:
        # Extract text content from markdown
        text_content = result.markdown_content
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=200,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", "?", "!", " ", ""]
        )
        chunks = text_splitter.split_text(text_content)
        
        # Generate embeddings and prepare data for Pinecone
        documents = []
        embeddings = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            # Generate embedding for this chunk
            embedding = generate_embedding_from_text(chunk)
            
            # Create unique ID for this chunk
            chunk_id = f"{result.url}_{i}"
            
            # Prepare metadata
            metadata = {
                "url": result.url,
                "title": result.title,
                "timestamp": result.timestamp,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "text": chunk
            }
            
            # Add to lists
            documents.append(chunk)
            embeddings.append(embedding)
            metadatas.append(metadata)
            ids.append(chunk_id)
        
        # Add to Pinecone in batches
        batch_size = 100  # Adjust based on your needs
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            
            index.upsert(
                vectors=zip(batch_ids, batch_embeddings, batch_metadatas)
            )

def retrieve_context(query: str) -> list[dict[str, str]]:
    query_embedding = generate_embedding_from_text(query)

    response = index.query(
        vector=query_embedding,
        top_k=4,
        include_metadata=True
    )

    results = []
    for match in response:
        metadata = match.metadata

        results.append({"url": metadata["url"], "text": metadata["text"]})

    return results