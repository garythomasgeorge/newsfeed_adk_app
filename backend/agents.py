import asyncio
import feedparser
from typing import List
from .models import Article, BiasLabel, ProcessingStatus
from datetime import datetime, timedelta
import ssl

# Bypass SSL verification for local dev issues
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

class HarvesterAgent:
    def __init__(self, feeds: dict):
        self.feeds = feeds

    async def fetch_new_articles(self) -> List[Article]:
        """
        Iterates through categorized feeds and collects raw article data.
        Returns Article objects with PENDING status.
        """
        articles = []
        # Allow articles from the last 48 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=48)
        print(f"Fetching articles published after: {cutoff_time}", flush=True)
        
        MAX_PER_CATEGORY = 12
        loop = asyncio.get_event_loop()
        
        for category, urls in self.feeds.items():
            print(f"--- Fetching Category: {category} ---", flush=True)
            category_count = 0
            
            for feed_url in urls:
                if category_count >= MAX_PER_CATEGORY:
                    break
                    
                try:
                    print(f"Checking feed: {feed_url}", flush=True)
                    # Run blocking feedparser in a thread
                    feed = await loop.run_in_executor(None, feedparser.parse, feed_url)
                    
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
                            # Create Article object with PENDING status
                            article = Article(
                                url=entry.get("link", ""),
                                headline=entry.get("title", ""),
                                summary="Processing...", # Placeholder
                                tldr_summary="Processing...",
                                detailed_summary="Analysis in progress...",
                                bias_label=BiasLabel.NOT_AVAILABLE,
                                topic_tags=[category], # Initial tag from category
                                processing_status=ProcessingStatus.PENDING,
                                created_at=published_dt,
                                expire_at=datetime.utcnow() + timedelta(days=7)
                            )
                            
                            if article.url and article.headline:
                                articles.append(article)
                                category_count += 1
                        else:
                            # print(f"Skipping old: {entry.get('title')[:20]}...")
                            pass
                except Exception as e:
                    print(f"Error fetching feed {feed_url}: {e}", flush=True)
            
            print(f"Fetched {category_count} articles for {category}", flush=True)
                
        print(f"Found {len(articles)} articles in total.", flush=True)
        return articles

import google.generativeai as genai
import os
import json
import requests
from bs4 import BeautifulSoup

class AnalystAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            print("Warning: Gemini API Key not provided.")


    async def process_article(self, article: Article) -> Article:
        """
        Analyzes a pending article using Gemini to generate summary, bias, and tags.
        Returns the updated Article object.
        """
        if not self.model:
            print("Gemini API Key missing. Skipping analysis.")
            article.processing_status = ProcessingStatus.FAILED
            article.summary = "Summary unavailable (No API Key)"
            article.tldr_summary = "Summary unavailable (No API Key)"
            article.detailed_summary = "Summary unavailable (No API Key)"
            return article

        # We need the full text, but for now we'll use the summary/headline if full text scraping isn't implemented
        # In a real app, we'd fetch the URL content here.
        # For this MVP, we'll assume the 'summary' field from RSS (which we put in 'summary' initially?) 
        # Wait, Harvester now puts "Processing..." in summary. 
        # We need to pass the raw description if we want to summarize it, OR fetch the URL.
        # Since we don't have a scraper for full text yet, let's assume we fetch the URL content 
        # OR we rely on the headline for now if we can't fetch.
        
        # Let's try to fetch the URL content simply
        
        text = ""
        try:
            # Simple fetch (blocking, should be async or in thread)
            loop = asyncio.get_event_loop()
            def fetch_text():
                try:
                    resp = requests.get(article.url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    paragraphs = soup.find_all('p')
                    return " ".join([p.get_text() for p in paragraphs])[:4000]
                except:
                    return ""
            
            text = await loop.run_in_executor(None, fetch_text)
        except Exception as e:
            print(f"Error fetching URL {article.url}: {e}")
            
        if not text:
            text = article.headline # Fallback to headline
            
        prompt = f"""
        Analyze the following news article text and provide a structured summary.
        
        Article Text:
        {text[:4000]}
        
        Output must be valid JSON with the following fields:
        - "headline": A catchy, neutral headline (or keep original if good).
        - "tldr": A 2-3 sentence quick summary (max 50 words).
        - "detailed_summary": A structured summary with 3 sections: "What Happened", "Impact/Reactions", and "Conclusion". Total length should be 150-200 words. Use Markdown formatting for the sections (e.g. **What Happened**: ...).
        - "bias_label": One of "Left", "Center", "Right".
        - "topic_tags": A list of 3-5 relevant tags.
        
        JSON Output:
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Clean up potential markdown code blocks in response
            content = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            
            # Update the existing article object
            article.headline = data.get("headline", article.headline)
            article.summary = data.get("tldr", "")
            article.tldr_summary = data.get("tldr", "")
            article.detailed_summary = data.get("detailed_summary", "")
            article.bias_label = BiasLabel(data.get("bias_label", "Center"))
            # Merge tags
            new_tags = data.get("topic_tags", [])
            article.topic_tags = list(set(article.topic_tags + new_tags))
            article.processing_status = ProcessingStatus.PROCESSED
            
            return article
        except Exception as e:
            print(f"Error analyzing article {article.url}: {e}")
            article.processing_status = ProcessingStatus.FAILED
            return article

class LibrarianAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    async def translate_query(self, natural_language_query: str) -> dict:
        """
        Translates natural language to Firestore query parameters.
        """
        if not self.model:
            return {}

        prompt = f"""
        Translate the following user search query into structured filters for a news database.
        Query: "{natural_language_query}"

        Available fields:
        - keywords (list of strings)
        - topic_tags (list of strings, e.g., "Technology", "Politics", "Sports")
        - bias_label (string: "Left", "Center", "Right", or null)

        Output JSON format:
        {{
            "keywords": ["..."],
            "topic_tags": ["..."],
            "bias_label": "..."
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            return json.loads(text)
        except Exception as e:
            print(f"Error translating query: {e}")
            return {"keywords": [natural_language_query]}
