import os
import json
import asyncio
from typing import List, Dict, Any
from google.adk import Agent
from google.adk.tools import AgentTool
import google.generativeai as genai

from .models import Article, BiasLabel, ProcessingStatus
from .tools import fetch_rss_articles, scrape_article_content

# Configure GenAI (ensure API key is set)
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

class HarvesterAgent(Agent):
    """
    Agent responsible for fetching news articles from RSS feeds.
    """
    def __init__(self, feeds: Dict[str, List[str]]):
        super().__init__(
            name="Harvester",
            model="gemini-2.0-flash",
            tools=[],
            instruction="You are a news harvester. Your goal is to fetch the latest articles from the provided RSS feeds."
        )
        # Store feeds AFTER calling super().__init__ to avoid Pydantic clearing them
        self._feeds = feeds

    def fetch_new_articles(self) -> List[Article]:
        raw_articles = fetch_rss_articles(self._feeds)
        articles = []
        for data in raw_articles:
            article = Article(
                url=data["url"],
                headline=data["headline"],
                summary=data["summary"],
                tldr_summary=None,
                detailed_summary=None,
                bias_label=BiasLabel.NOT_AVAILABLE,
                topic_tags=data["topic_tags"],
                processing_status=ProcessingStatus.PENDING,
                created_at=datetime.fromisoformat(data["created_at"]),
                expire_at=datetime.utcnow() + timedelta(days=7)
            )
            articles.append(article)
        return articles

from datetime import datetime, timedelta

class AnalystAgent(Agent):
    """
    Agent responsible for analyzing articles, summarizing them, and detecting bias.
    """
    def __init__(self):
        super().__init__(
            name="Analyst",
            model="gemini-2.0-flash",
            tools=[],
            instruction="""You are an expert news analyst. Your job is to analyze news articles.
            When given an article URL and summary:
            1. Scrape the full content if possible.
            2. Analyze the text for bias.
            3. Generate a structured summary (TLDR and Detailed).
            4. Extract keywords and tags.
            
            Output must be valid JSON matching the schema provided in the prompt."""
        )
        # Create a GenerativeModel for direct LLM calls (AFTER super init to avoid Pydantic clearing it)
        self._model = genai.GenerativeModel('gemini-2.0-flash')

    async def process_article(self, article: Article) -> Article:
        prompt = f"""
        Analyze this article:
        URL: {article.url}
        Headline: {article.headline}
        Initial Summary: {article.summary}
        
        Use the scrape_article_content tool to get the full text.
        
        Then provide a JSON output with:
        - "headline": (str)
        - "tldr": (str, max 50 words)
        - "detailed_summary": (str, markdown with sections: What Happened, Impact, Conclusion)
        - "bias_label": (str, one of "Left", "Lean Left", "Center", "Lean Right", "Right")
        - "topic_tags": (list of str)
        - "keywords": (list of str)
        """
        
        try:
            response = self._model.generate_content(prompt)
            text = response.text if hasattr(response, 'text') else str(response)
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
                
            data = json.loads(text)
            
            article.headline = data.get("headline", article.headline)
            article.tldr_summary = data.get("tldr", "")
            article.detailed_summary = data.get("detailed_summary", "")
            article.bias_label = BiasLabel(data.get("bias_label", "Center"))
            article.topic_tags = list(set(article.topic_tags + data.get("topic_tags", [])))
            article.keywords = data.get("keywords", [])
            article.processing_status = ProcessingStatus.PROCESSED
            
        except Exception as e:
            print(f"Error analyzing article {article.url}: {e}")
            article.processing_status = ProcessingStatus.FAILED
            
        return article

class NewsChiefAgent(Agent):
    """
    Root agent that orchestrates the news gathering and processing.
    """
    def __init__(self, harvester: HarvesterAgent, analyst: AnalystAgent):
        super().__init__(
            name="NewsChief",
            model="gemini-2.0-flash",
            tools=[],
            instruction="You are the Chief Editor. You manage the news feed."
        )
        # Store subagents AFTER calling super().__init__
        self._harvester = harvester
        self._analyst = analyst

    async def refresh_news(self) -> Dict[str, int]:
        print("Chief: Starting news refresh cycle...")
        articles = self._harvester.fetch_new_articles()
        print(f"Chief: Harvester found {len(articles)} articles.")
        
        processed_count = 0
        failed_count = 0
        sem = asyncio.Semaphore(5)
        
        async def process(art):
            nonlocal processed_count, failed_count
            async with sem:
                res = await self._analyst.process_article(art)
                if res.processing_status == ProcessingStatus.PROCESSED:
                    processed_count += 1
                else:
                    failed_count += 1
                return res

        tasks = [process(a) for a in articles]
        processed_articles = await asyncio.gather(*tasks)
        
        print(f"Chief: Finished processing. Success: {processed_count}, Failed: {failed_count}")
        return {"total": len(articles), "processed": processed_count, "failed": failed_count, "articles": processed_articles}

class LibrarianAgent(Agent):
    """
    Agent responsible for translating natural language queries into database filters.
    """
    def __init__(self):
        super().__init__(
            name="Librarian",
            model="gemini-2.0-flash",
            tools=[],
            instruction="""You are a librarian. Translate user search queries into structured filters.
            Available fields: keywords (list), topic_tags (list), bias_label (str).
            Output JSON."""
        )
        # Create a GenerativeModel for direct LLM calls (AFTER super init to avoid Pydantic clearing it)
        self._model = genai.GenerativeModel('gemini-2.0-flash')

    async def translate_query(self, natural_language_query: str) -> dict:
        prompt = f"""
        Translate query: "{natural_language_query}"
        Output JSON format: {{ "keywords": [], "topic_tags": [], "bias_label": "" }}
        """
        try:
            response = self._model.generate_content(prompt)
            text = response.text if hasattr(response, 'text') else str(response)
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text.strip())
        except Exception as e:
            print(f"Error translating query: {e}")
            return {"keywords": [natural_language_query]}
