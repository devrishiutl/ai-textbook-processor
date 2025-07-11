import chromadb
import uuid
import os

# Initialize ChromaDB with persistent storage
persist_directory = "./chroma_db"
os.makedirs(persist_directory, exist_ok=True)
client = chromadb.PersistentClient(path=persist_directory)
def store_textbook_transcript(standard, subject, chapter, content, content_type):

    collection = client.get_or_create_collection("textbook_transcripts")

    # Generate a UUID for this record
    content_id = str(uuid.uuid4())

    # Store the content with full metadata
    collection.add(
        documents=[content],
        metadatas=[{
            "standard": standard,
            "subject": subject,
            "chapter": chapter,
            "content_type": content_type
        }],
        ids=[content_id]
    )
    
    # Verify the content was stored
    result = collection.get(ids=[content_id])
    if result["ids"]:
        return content_id
    return None
            


def get_textbook_transcript(ids):

    # Retrieve content by ID
    collection = client.get_or_create_collection("textbook_transcripts")
    result = collection.get(ids=[ids])
    
    if result["ids"] and len(result["ids"]) > 0:
        return result["documents"][0]  # Return the first document
    return None



    
