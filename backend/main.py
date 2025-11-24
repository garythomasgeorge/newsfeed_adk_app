import os
from fastapi import FastAPI, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List
from .models import Article, SearchRequest, ProcessingStatus
from .agents import HarvesterAgent, AnalystAgent, LibrarianAgent
from .database import get_recent_articles, save_article, search_articles_by_query
from dotenv import load_dotenv

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI News Aggregator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agents
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FEEDS = {
    "Politics": [
        "http://feeds.bbci.co.uk/news/politics/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml"
    ],
    "International": [
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml"
    ],
    "Entertainment": [
        "https://www.eonline.com/news/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Movies.xml"
    ],
    "Sports": [
        "https://www.espn.com/espn/rss/news",
        "http://feeds.bbci.co.uk/sport/rss.xml"
    ]
}

harvester = HarvesterAgent(feeds=FEEDS)
analyst = AnalystAgent(api_key=GEMINI_API_KEY)
librarian = LibrarianAgent(api_key=GEMINI_API_KEY)

import asyncio

@app.post("/api/batch-ingest")
async def batch_ingest():
    """
    Phase 1: Harvests articles from RSS feeds and saves them as PENDING.
    This is fast and non-blocking.
    """
    print("Starting Harvest...")
    articles = await harvester.fetch_new_articles()
    print(f"Harvested {len(articles)} articles. Saving to DB...", flush=True)
    
    saved_count = 0
    for article in articles:
        await save_article(article)
        saved_count += 1
        
    print(f"Harvest complete. Saved {saved_count} pending articles.", flush=True)
    
    # Trigger background processing
    asyncio.create_task(process_background_queue())
    
    return {"status": "success", "harvested": saved_count, "message": "Harvest complete. Background processing started."}

@app.post("/api/process-queue")
async def trigger_process_queue(background_tasks: BackgroundTasks):
    """
    Phase 2: Manually triggers processing of pending articles.
    """
    background_tasks.add_task(process_background_queue)
    return {"status": "success", "message": "Processing queue started in background."}

async def process_background_queue():
    """
    Background task to process pending articles.
    """
    print("Starting background processing queue...", flush=True)
    from .database import get_pending_articles
    
    pending_articles_data = await get_pending_articles(limit=10)
    print(f"Found {len(pending_articles_data)} pending articles.", flush=True)
    
    if not pending_articles_data:
        return

    # Convert dicts back to Article objects
    pending_articles = []
    for data in pending_articles_data:
        try:
            pending_articles.append(Article(**data))
        except Exception as e:
            print(f"Error parsing article data: {e}")

    sem = asyncio.Semaphore(3) # Limit concurrency for AI calls

    async def process_single(article: Article):
        async with sem:
            try:
                print(f"Processing: {article.headline[:30]}...", flush=True)
                # Add timeout per article
                updated_article = await asyncio.wait_for(analyst.process_article(article), timeout=45.0)
                if updated_article:
                    await save_article(updated_article)
                    print(f"Completed: {updated_article.headline[:30]}...", flush=True)
                    return 1
            except asyncio.TimeoutError:
                print(f"Timeout processing article: {article.headline[:30]}...", flush=True)
                # Mark as failed or leave as pending? Let's mark failed for now to avoid infinite loop
                article.processing_status = ProcessingStatus.FAILED
                await save_article(article)
            except Exception as e:
                print(f"Error processing article {article.url}: {e}", flush=True)
            return 0

    tasks = [process_single(article) for article in pending_articles]
    results = await asyncio.gather(*tasks)
    processed_count = sum(results)
    
    print(f"Queue processing complete. Processed {processed_count} articles.", flush=True)
    
    # Recursively call if there might be more (optional, but good for clearing queue)
    if len(pending_articles) == 10:
        print("More articles likely pending, continuing queue...", flush=True)
        await process_background_queue()

@app.get("/api/feed")
async def get_feed(date: str = None):
    """
    Get the news feed. Optional 'date' param in YYYY-MM-DD format.
    """
    filter_date = None
    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            pass # Ignore invalid date format
            
    return await get_recent_articles(filter_date=filter_date)

@app.get("/api/available-dates")
async def get_available_dates():
    """
    Returns a list of dates (YYYY-MM-DD) that have articles.
    """
    from .database import get_available_dates as db_get_dates
    dates = await db_get_dates()
    return dates

@app.post("/api/search")
async def search_articles(request: SearchRequest):
    """
    Natural language search via Librarian Agent.
    """
    query_params = await librarian.translate_query(request.query)
    results = await search_articles_by_query(query_params)
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
