import chromadb
from chromadb.utils import embedding_functions
import os

# Use a local directory for Chroma persistence
CHROMA_DATA_PATH = "ai/chroma_db"
os.makedirs(CHROMA_DATA_PATH, exist_ok=True)

client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
# Use default embedding function for now
emb_fn = embedding_functions.DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name="college0_info",
    embedding_function=emb_fn
)

def seed_vector_store():
    # Example documents about college rules
    docs = [
        {"id": "rule_1", "text": "Students must register for 2 to 4 courses per semester.", "metadata": {"role": "all"}},
        {"id": "rule_2", "text": "GPA below 2.0 results in automatic termination.", "metadata": {"role": "student"}},
        {"id": "rule_3", "text": "A student receives a warning for reviews containing taboo words.", "metadata": {"role": "student"}},
        {"id": "rule_4", "text": "Instructors are suspended if they accumulate 3 warnings.", "metadata": {"role": "instructor"}},
        {"id": "rule_5", "text": "Courses with fewer than 3 enrolled students are cancelled in Period 3.", "metadata": {"role": "all"}},
        {"id": "grad_1", "text": "Students who complete 8 courses can apply for graduation.", "metadata": {"role": "student"}},
    ]
    
    collection.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[d["metadata"] for d in docs]
    )
    print("Vector store seeded!")

def query_vector_store(query_text, user_role='visitor'):
    results = collection.query(
        query_texts=[query_text],
        n_results=1,
        # In a real app, we'd filter by metadata based on role
    )
    
    if results['documents'] and results['distances'][0][0] < 0.5: # Threshold
        return results['documents'][0][0]
    return None

if __name__ == "__main__":
    seed_vector_store()
