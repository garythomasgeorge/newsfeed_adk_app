import asyncio
import os
from dotenv import load_dotenv
from backend.agents import AnalystAgent
from backend.models import Article, BiasLabel, ProcessingStatus
from backend.database import save_article, get_backfill_candidates
from datetime import datetime, timedelta

# Load environment variables
load_dotenv("backend/.env")

async def test_processing():
    print("Testing article processing...")
    
    # Get API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: No API key found!")
        return
    
    print(f"API Key found: {api_key[:10]}...")
    
    # Initialize agent
    analyst = AnalystAgent(api_key)
    print(f"Analyst initialized with model: {analyst.model}")
    
    # Get one candidate
    candidates = await get_backfill_candidates(limit=1)
    if not candidates:
        print("No candidates found!")
        return
        
    print(f"Found candidate: {candidates[0].get('headline')}")
    
    # Convert to Article
    article = Article(**candidates[0])
    print(f"Article status before: {article.processing_status}")
    print(f"Article keywords before: {article.keywords}")
    
    # Process it
    try:
        print("Processing article...")
        processed = await analyst.process_article(article)
        print(f"Article status after: {processed.processing_status}")
        print(f"Article keywords after: {processed.keywords}")
        print(f"Article bias: {processed.bias_label}")
        
        # Save it
        print("Saving article...")
        await save_article(processed)
        print("Article saved successfully!")
        
    except Exception as e:
        print(f"ERROR during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_processing())
