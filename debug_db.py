import asyncio
from backend.database import get_recent_articles, db, COLLECTION_NAME

async def check_db():
    print(f"Checking Firestore Collection: {COLLECTION_NAME}")
    if not db:
        print("! Firestore Client NOT initialized.")
        return

    # Check count (approx)
    docs = db.collection(COLLECTION_NAME).limit(5).stream()
    count = 0
    for doc in docs:
        count += 1
        print(f"Found Doc ID: {doc.id}")
        data = doc.to_dict()
        print(f"  - Headline: {data.get('headline')}")
        print(f"  - Created At: {data.get('created_at')}")
    
    if count == 0:
        print("! No documents found in collection.")
    else:
        print(f"Found at least {count} documents.")

    print("\nTesting get_recent_articles()...")
    recent = await get_recent_articles()
    print(f"get_recent_articles returned {len(recent)} items.")

if __name__ == "__main__":
    asyncio.run(check_db())
