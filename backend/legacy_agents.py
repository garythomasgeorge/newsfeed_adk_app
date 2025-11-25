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
                                summary=entry.get("summary") or entry.get("description") or "Summary unavailable",
                                tldr_summary=None, # Will be generated
                                detailed_summary=None, # Will be generated
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
            self.model = genai.GenerativeModel('gemini-2.0-flash')
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
        
        # Blocking phrases common in paywalls/anti-bot pages
        BLOCKING_PHRASES = [
            "enable javascript",
            "disable ad blocker",
            "turn off your ad blocker",
            "subscribe to read",
            "subscription required",
            "sign in to continue",
            "you have reached your limit",
            "access to this content is restricted",
            "please enable cookies"
        ]

        text = ""
        try:
            # Simple fetch (blocking, should be async or in thread)
            loop = asyncio.get_event_loop()
            def fetch_text():
                try:
                    resp = requests.get(article.url, timeout=5, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"})
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                        
                    paragraphs = soup.find_all('p')
                    content = " ".join([p.get_text() for p in paragraphs])
                    return content[:5000] # Limit to 5000 chars
                except:
                    return ""
            
            text = await loop.run_in_executor(None, fetch_text)
            
            # Check for blocking content
            text_lower = text.lower()
            is_blocked = False
            if len(text) < 200: # Too short, likely failed or just a blurb
                is_blocked = True
            else:
                for phrase in BLOCKING_PHRASES:
                    if phrase in text_lower:
                        is_blocked = True
                        break
            
            if is_blocked:
                print(f"Content blocked or too short for {article.url}. Using RSS summary fallback.")
                text = article.summary # Fallback to RSS summary
                
        except Exception as e:
            print(f"Error fetching URL {article.url}: {e}")
            text = article.summary
            
        if not text or len(text) < 50:
            text = f"{article.headline}. {article.summary}" # Fallback to headline + summary
            
        # Load known bias
        known_bias_label = "Unknown"
        try:
            from urllib.parse import urlparse
            domain = urlparse(article.url).netloc.replace("www.", "")
            
            # Load bias map (cache this in production)
            import pathlib
            # Get the directory where this file (agents.py) is located
            current_dir = pathlib.Path(__file__).parent.absolute()
            bias_file = current_dir / "known_bias.json"
            
            if bias_file.exists():
                with open(bias_file, "r") as f:
                    bias_map = json.load(f)
                    
                # Check for exact match or substring match
                if domain in bias_map:
                    known_bias_label = bias_map[domain]
                else:
                    # Try to find partial match (e.g. edition.cnn.com -> cnn.com)
                    for key, val in bias_map.items():
                        if key in domain:
                            known_bias_label = val
                            break
            else:
                print(f"Warning: Bias file not found at {bias_file}")
        except Exception as e:
            print(f"Error loading known bias: {e}")

        prompt = f"""
        Analyze the following news article text and provide a structured summary.
        
        Context:
        - Source Domain: {domain}
        - Typical Source Bias: {known_bias_label} (Use this as a baseline, but evaluate the specific text. If the text is neutral despite the source, label it 'Center'. If it reflects the source's bias, label it accordingly.)
        
        Article Text:
        {text[:4000]}
        
        Output must be valid JSON with the following fields:
        - "headline": A catchy, neutral headline (or keep original if good).
        - "tldr": A 2-3 sentence quick summary (max 50 words).
        - "detailed_summary": A structured summary with 3 sections: "What Happened", "Impact/Reactions", and "Conclusion". Total length should be 150-200 words. Use Markdown formatting for the sections (e.g. **What Happened**: ...).
        - "bias_label": One of "Left", "Lean Left", "Center", "Lean Right", "Right".
        - "bias_label": One of "Left", "Lean Left", "Center", "Lean Right", "Right".
        - "topic_tags": A list of 3-5 relevant tags.
        - "keywords": A list of 3-5 specific entities (people, places, organizations) mentioned.
        
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
            article.keywords = data.get("keywords", [])
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
            self.model = genai.GenerativeModel('gemini-2.0-flash')
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
