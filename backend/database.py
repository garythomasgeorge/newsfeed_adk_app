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

async def get_backfill_candidates(limit: int = 50) -> List[dict]:
    """
    Retrieves articles that need processing.
    This includes:
    1. Articles with processing_status='pending'
    2. Articles where detailed_summary is missing or empty (legacy data)
    """
    if not db:
        return []
        
    candidates = []
    try:
        # 1. Fetch pending
        pending_docs = db.collection(COLLECTION_NAME)\
                 .where("processing_status", "==", "pending")\
                 .limit(limit)\
                 .stream()
        
        for doc in pending_docs:
            candidates.append(doc.to_dict())
            
        if len(candidates) >= limit:
            return candidates

        # 2. Fetch missing summaries (legacy)
        # Note: Firestore doesn't support "where field is null" or "where field is empty string" easily combined with other filters
        # We'll fetch recent articles and filter in memory for this backfill task
        recent_docs = db.collection(COLLECTION_NAME)\
                 .order_by("created_at", direction=firestore.Query.DESCENDING)\
                 .limit(100)\
                 .stream()
                 
        for doc in recent_docs:
            data = doc.to_dict()
            # Check if it's already in candidates
            if any(c['url'] == data['url'] for c in candidates):
                continue
                
            # Check if it needs processing
            status = data.get("processing_status")
            summary = data.get("detailed_summary")
            keywords = data.get("keywords")
            
            # Criteria for backfill:
            # 1. Not processed (legacy or pending)
            # 2. Missing summary
            # 3. Missing keywords (new feature)
            needs_update = False
            
            if status != "processed":
                needs_update = True
            elif not summary or len(summary) < 10:
                needs_update = True
            elif not keywords or len(keywords) == 0:
                needs_update = True
                
            if needs_update:
                candidates.append(data)
                if len(candidates) >= limit:
                    break
                    
        return candidates
    except Exception as e:
        print(f"Error retrieving backfill candidates: {e}")
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

async def find_similar_articles(article_id: str, limit: int = 5) -> List[dict]:
    """
    Finds similar articles based on topic tags.
    Prioritizes articles with different bias labels to show diverse perspectives.
    """
    if not db:
        return []
        
    try:
        # 1. Get the target article
        # article_id is the URL (encoded or raw? The frontend passes the full URL usually)
        # In save_article we use url.replace("/", "_") as ID. 
        # Let's try to find it by ID first, if not, query by URL.
        
        # Assuming article_id passed from frontend is the actual URL
        target_ref = db.collection(COLLECTION_NAME).where("url", "==", article_id).limit(1).stream()
        target_doc = next(target_ref, None)
        
        if not target_doc:
            print(f"Target article not found: {article_id}")
            return []
            
        target_data = target_doc.to_dict()
        target_tags = target_data.get("topic_tags", [])
        target_keywords = target_data.get("keywords", [])
        target_bias = target_data.get("bias_label", "Center")
        target_domain = ""
        try:
            from urllib.parse import urlparse
            target_domain = urlparse(target_data["url"]).netloc.replace("www.", "")
        except:
            pass
        
        if not target_tags and not target_keywords:
            return []
            
        # 2. Query for articles with matching keywords OR tags
        # Firestore limitation: can't do OR across different fields easily or multiple array-contains
        # We'll prioritize keywords if available, otherwise tags
        
        candidates = []
        seen_urls = set()
        seen_urls.add(target_data["url"])
        
        # Helper to process results
        def process_results(docs):
            for doc in docs:
                data = doc.to_dict()
                url = data.get("url", "")
                if url in seen_urls:
                    continue
                    
                # Strict Domain Filter
                try:
                    domain = urlparse(url).netloc.replace("www.", "")
                    if domain == target_domain:
                        continue
                except:
                    pass
                    
                candidates.append(data)
                seen_urls.add(url)

        # Query by keywords first (more specific)
        if target_keywords:
            keyword_docs = db.collection(COLLECTION_NAME)\
                             .where("keywords", "array_contains_any", target_keywords[:10])\
                             .limit(20)\
                             .stream()
            process_results(keyword_docs)
            
        # If not enough, query by tags
        if len(candidates) < limit and target_tags:
            tag_docs = db.collection(COLLECTION_NAME)\
                         .where("topic_tags", "array_contains_any", target_tags)\
                         .limit(20)\
                         .stream()
            process_results(tag_docs)
            
        # 3. Sort/Filter for diversity
        # We want to show articles that match tags but have DIFFERENT bias if possible.
        
        def diversity_score(article):
            score = 0
            # Higher score if bias is different
            if article.get("bias_label") != target_bias:
                score += 10
            # Keyword match boost
            common_keywords = set(article.get("keywords", [])) & set(target_keywords)
            score += len(common_keywords) * 5
            # Tag match boost
            common_tags = set(article.get("topic_tags", [])) & set(target_tags)
            score += len(common_tags)
            return score
            
        candidates.sort(key=diversity_score, reverse=True)
        
        return candidates[:limit]
        
    except Exception as e:
        print(f"Error finding similar articles: {e}")
        return []
