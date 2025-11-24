import os
from google.cloud import firestore
from datetime import datetime, timedelta
from typing import List, Optional
from .models import Article

# Initialize Firestore client
# Note: In a real deployment, credentials would be handled by the environment or default credentials
try:
    db = firestore.Client()
except Exception as e:
    print(f"Warning: Firestore client could not be initialized: {e}")
    db = None

COLLECTION_NAME = "articles"

def get_firestore_client():
    return db

async def save_article(article: Article):
    if not db:
        print("Firestore DB not initialized")
        return
    
    doc_ref = db.collection(COLLECTION_NAME).document(article.url.replace("/", "_")) # Simple encoding for ID
    doc_ref.set(article.dict())

async def get_recent_articles(limit: int = 50, filter_date: datetime.date = None):
    """
    Retrieves the most recent articles from Firestore.
    If filter_date is provided, filters by that specific date (UTC).
    """
    if not db:
        return []
        
    try:
        articles_ref = db.collection(COLLECTION_NAME)
        
        if filter_date:
            # Create start and end of the day timestamps
            start_of_day = datetime.combine(filter_date, datetime.min.time())
            end_of_day = datetime.combine(filter_date, datetime.max.time())
            
            query = articles_ref.where(
                "created_at", ">=", start_of_day
            ).where(
                "created_at", "<=", end_of_day
            ).order_by(
                "created_at", direction=firestore.Query.DESCENDING
            )
        else:
            query = articles_ref.order_by(
                "created_at", direction=firestore.Query.DESCENDING
            )
            
        docs = query.limit(limit).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"Error retrieving articles: {e}")
        return []

async def get_pending_articles(limit: int = 10) -> List[dict]:
    """
    Retrieves articles with processing_status='pending'.
    """
    if not db:
        return []
    
    try:
        docs = db.collection(COLLECTION_NAME)\
                 .where("processing_status", "==", "pending")\
                 .limit(limit)\
                 .stream()
        
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"Error retrieving pending articles: {e}")
        return []

async def get_available_dates() -> List[str]:
    """
    Retrieves a list of unique dates (YYYY-MM-DD) from stored articles.
    Note: Firestore doesn't support 'SELECT DISTINCT' natively efficiently.
    For high volume, we'd aggregate this in a separate collection.
    For this MVP, we'll fetch recent article dates.
    """
    if not db:
        return []
        
    try:
        # Optimization: Just fetch the 'created_at' field for the last 500 articles
        # and extract unique dates.
        docs = db.collection(COLLECTION_NAME)\
                 .order_by("created_at", direction=firestore.Query.DESCENDING)\
                 .limit(500)\
                 .select(["created_at"])\
                 .stream()
        
        dates = set()
        for doc in docs:
            data = doc.to_dict()
            if "created_at" in data:
                # Handle both datetime object and string (if serialized)
                created_at = data["created_at"]
                if hasattr(created_at, "date"):
                    dates.add(created_at.date().isoformat())
                elif isinstance(created_at, str):
                     dates.add(created_at[:10])
        
        return sorted(list(dates), reverse=True)
    except Exception as e:
        print(f"Error retrieving available dates: {e}")
        return []

async def search_articles_by_query(query_params: dict) -> List[dict]:
    """
    Executes a constructed query against Firestore.
    """
    if not db:
        return []
    
    ref = db.collection(COLLECTION_NAME)
    
    # Apply filters
    if query_params.get("bias_label"):
        ref = ref.where("bias_label", "==", query_params["bias_label"])
        
    if query_params.get("topic_tags"):
        # Firestore allows 'array_contains_any' for list fields
        ref = ref.where("topic_tags", "array_contains_any", query_params["topic_tags"])
        
    # Note: Firestore has limitations on compound queries. 
    # For this MVP, we'll prioritize topic tags and bias.
    # Full text search on 'keywords' is not supported natively by Firestore.
    
    docs = ref.order_by("created_at", direction=firestore.Query.DESCENDING).limit(20).stream()
    
    return [doc.to_dict() for doc in docs]
