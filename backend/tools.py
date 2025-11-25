import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Any
import ssl
import asyncio

# Bypass SSL verification for local dev issues
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

def fetch_rss_articles(feeds: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Fetches articles from the provided RSS feeds.
    Returns a list of article dictionaries.
    """
    articles = []
    cutoff_time = datetime.utcnow() - timedelta(hours=48)
    MAX_PER_CATEGORY = 12
    
    print(f"Fetching articles published after: {cutoff_time}", flush=True)
    
    for category, urls in feeds.items():
        print(f"--- Fetching Category: {category} ---", flush=True)
        category_count = 0
        
        for feed_url in urls:
            if category_count >= MAX_PER_CATEGORY:
                break
                
            try:
                print(f"Checking feed: {feed_url}", flush=True)
                # feedparser is blocking, but we are wrapping this in a function 
                # that can be called by an agent (potentially in a thread)
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    if category_count >= MAX_PER_CATEGORY:
                        break

                    # Parse date
                    published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
                    if not published_parsed:
                        continue
                        
                    # Convert struct_time to datetime
                    published_dt = datetime(*published_parsed[:6])
                    
                    # Filter for last 48 hours
                    if published_dt >= cutoff_time:
                        article_data = {
                            "url": entry.get("link", ""),
                            "headline": entry.get("title", ""),
                            "summary": entry.get("summary") or entry.get("description") or "Summary unavailable",
                            "topic_tags": [category],
                            "created_at": published_dt.isoformat()
                        }
                        
                        if article_data["url"] and article_data["headline"]:
                            articles.append(article_data)
                            category_count += 1
            except Exception as e:
                print(f"Error fetching feed {feed_url}: {e}", flush=True)
        
        print(f"Fetched {category_count} articles for {category}", flush=True)
            
    print(f"Found {len(articles)} articles in total.", flush=True)
    return articles

def scrape_article_content(url: str, fallback_summary: str = "") -> str:
    """
    Fetches the full text content of an article URL.
    """
    BLOCKING_PHRASES = [
        "enable javascript", "disable ad blocker", "turn off your ad blocker",
        "subscribe to read", "subscription required", "sign in to continue",
        "you have reached your limit", "access to this content is restricted",
        "please enable cookies"
    ]

    try:
        resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"})
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text() for p in paragraphs])
        text = content[:5000] # Limit to 5000 chars
        
        # Check for blocking content
        text_lower = text.lower()
        is_blocked = False
        if len(text) < 200:
            is_blocked = True
        else:
            for phrase in BLOCKING_PHRASES:
                if phrase in text_lower:
                    is_blocked = True
                    break
        
        if is_blocked:
            print(f"Content blocked or too short for {url}. Using fallback.")
            return fallback_summary
            
        return text
            
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        return fallback_summary
