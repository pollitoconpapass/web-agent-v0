import os
import ollama
from dotenv import load_dotenv
from pinecone import Pinecone
from crawl4ai.models import CrawlResult
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

def generate_embedding_from_text(text: str) -> list[float]:
    response = ollama.embed(model="nomic-embed-text", input=text)
    embedding = response["embeddings"]

    if embedding[0] and isinstance(embedding[0], list):
        embedding = [item for sublist in embedding for item in sublist]
    return embedding

def normalize_urls(url):
    normalized_url = (
        url.replace("https://", "")
        .replace("www.", "")
        .replace("/", "_")
        .replace("-", "_")
        .replace(".", "_")
    )

    return normalized_url

def add_text_to_index(results: list[CrawlResult]):
    for result in results:
        if result is None or result.markdown_v2 is None:
            continue

        text_content = result.markdown_v2.fit_markdown
        
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
            embedding = generate_embedding_from_text(chunk)

            normalized_url = normalize_urls(result.url)
            chunk_id = f"{normalized_url}_{i}"

            
            metadata = {
                "url": normalized_url,
                # "title": result.title,
                # "timestamp": result.timestamp,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "text": chunk
            }

            if len(chunk) <= 3: # there are times when the chunk is too small like 2 words
                continue

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
    for match in response.matches:
        metadata = match.metadata

        results.append({"url": metadata["url"], "text": metadata["text"]})

    return results