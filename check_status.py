import asyncio
import os
from google.cloud import firestore
from backend.models import ProcessingStatus

# Initialize Firestore
db = firestore.Client()
COLLECTION_NAME = "articles"

async def check_status():
    print("Checking article status...")
    docs = db.collection(COLLECTION_NAME).stream()
    
    total = 0
    pending = 0
    processed = 0
    failed = 0
    with_keywords = 0
    without_keywords = 0
    
    for doc in docs:
        total += 1
        data = doc.to_dict()
        status = data.get("processing_status")
        keywords = data.get("keywords", [])
        
        if status == "pending":
            pending += 1
        elif status == "processed":
            processed += 1
        elif status == "failed":
            failed += 1
            
        if keywords:
            with_keywords += 1
        else:
            without_keywords += 1
            
    print(f"Total Articles: {total}")
    print(f"Pending: {pending}")
    print(f"Processed: {processed}")
    print(f"Failed: {failed}")
    print(f"With Keywords: {with_keywords}")
    print(f"Without Keywords: {without_keywords}")

if __name__ == "__main__":
    asyncio.run(check_status())
