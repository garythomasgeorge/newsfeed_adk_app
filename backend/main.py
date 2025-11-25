import os
import asyncio
from fastapi import FastAPI, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List
from .models import Article, SearchRequest, ProcessingStatus
from .agents import HarvesterAgent, AnalystAgent, LibrarianAgent, NewsChiefAgent
from .database import get_recent_articles, save_article, search_articles_by_query
from dotenv import load_dotenv

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pathlib

app = FastAPI(title="AI News Aggregator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
frontend_dist = pathlib.Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

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

# Instantiate ADK Agents
harvester = HarvesterAgent(feeds=FEEDS)
analyst = AnalystAgent() # API key is handled in agents.py via env or genai.configure
librarian = LibrarianAgent()
news_chief = NewsChiefAgent(harvester=harvester, analyst=analyst)

@app.post("/api/batch-ingest")
async def batch_ingest(background_tasks: BackgroundTasks):
    """
    Triggers the News Chief to refresh the news (harvest + analyze).
    Runs in background.
    """
    background_tasks.add_task(run_news_refresh)
    return {"status": "started", "message": "News Chief started refresh cycle in background."}

async def run_news_refresh():
    """
    Background task wrapper for News Chief.
    """
    print("Background: Triggering News Chief...", flush=True)
    try:
        result = await news_chief.refresh_news()
        
        # Save results to DB
        # The refresh_news returns processed articles, we should save them.
        # Note: Harvester creates PENDING articles, Analyst updates them.
        # We need to ensure they are saved.
        # In the new flow, NewsChief returns the list of articles.
        
        print(f"News Chief finished. Saving {len(result['articles'])} articles...", flush=True)
        for article in result['articles']:
            await save_article(article)
            
        print("News Chief cycle complete.", flush=True)
    except Exception as e:
        print(f"Error in News Chief cycle: {e}", flush=True)

@app.post("/api/process-queue")
async def process_queue(background_tasks: BackgroundTasks):
    """
    Legacy endpoint: Manually triggers processing of pending articles.
    We can map this to the Analyst directly or just ignore if Chief handles everything.
    For compatibility, let's implement a queue processor using the Analyst.
    """
    background_tasks.add_task(process_background_queue)
    return {"status": "processing_started", "message": "Background processing triggered."}

@app.post("/api/process-backfill")
async def process_backfill(background_tasks: BackgroundTasks):
    """
    Triggers a backfill process for older articles.
    """
    background_tasks.add_task(process_backfill_queue)
    return {"status": "backfill_started", "message": "Backfill processing triggered."}

async def process_backfill_queue():
    print("Starting backfill processing...", flush=True)
    from .database import get_backfill_candidates, save_article
    
    articles_data = await get_backfill_candidates(limit=20)
    print(f"Found {len(articles_data)} articles needing backfill.", flush=True)
    
    for article_data in articles_data:
        try:
            article = Article(**article_data)
            if article.processing_status != ProcessingStatus.PENDING:
                article.processing_status = ProcessingStatus.PENDING
            
            print(f"Backfilling article: {article.headline}", flush=True)
            try:
                processed_article = await asyncio.wait_for(
                    analyst.process_article(article),
                    timeout=30.0
                )
                await save_article(processed_article)
            except Exception as e:
                print(f"Error backfilling article {article.url}: {e}", flush=True)
                article.processing_status = ProcessingStatus.FAILED
                await save_article(article)
            
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Error preparing article for backfill: {e}", flush=True)

async def process_background_queue():
    print("Starting background processing queue...", flush=True)
    from .database import get_pending_articles
    
    pending_articles_data = await get_pending_articles(limit=10, statuses=["pending", "failed"])
    if not pending_articles_data:
        return

    pending_articles = [Article(**data) for data in pending_articles_data]
    
    sem = asyncio.Semaphore(3)

    async def process_single(article: Article):
        async with sem:
            try:
                print(f"Processing: {article.headline[:30]}...", flush=True)
                updated_article = await asyncio.wait_for(analyst.process_article(article), timeout=45.0)
                if updated_article:
                    await save_article(updated_article)
                    return 1
            except Exception as e:
                print(f"Error processing article {article.url}: {e}", flush=True)
                article.processing_status = ProcessingStatus.FAILED
                await save_article(article)
            return 0

    tasks = [process_single(article) for article in pending_articles]
    await asyncio.gather(*tasks)
    print("Queue processing complete.", flush=True)

@app.get("/api/feed")
async def get_feed(date: str = None):
    filter_date = None
    if date:
        try:
            from datetime import datetime
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            pass
    return await get_recent_articles(filter_date=filter_date)

@app.get("/api/available-dates")
async def get_available_dates():
    from .database import get_available_dates as db_get_dates
    return await db_get_dates()

@app.post("/api/search")
async def search_articles(request: SearchRequest):
    print(f"Searching for: {request.query}")
    filters = await librarian.translate_query(request.query)
    print(f"Filters: {filters}")
    
    from .database import search_articles_by_query
    results = await search_articles_by_query(filters)
    
    return {"filters": filters, "results": results}

@app.get("/api/articles/similar")
async def get_similar_articles(url: str):
    from .database import find_similar_articles
    results = await find_similar_articles(url)
    return results

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if full_path.startswith("api/"):
        return {"detail": "Not Found"}
    
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"detail": "Frontend not built"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
