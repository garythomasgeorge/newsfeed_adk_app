import feedparser
from datetime import datetime, timedelta

FEEDS = [
    "http://feeds.bbci.co.uk/news/politics/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.eonline.com/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Movies.xml",
    "https://www.espn.com/espn/rss/news",
    "http://feeds.bbci.co.uk/sport/rss.xml"
]

def debug_feeds():
    cutoff_time = datetime.utcnow() - timedelta(hours=48)
    print(f"DEBUG: Cutoff Time (UTC): {cutoff_time}")
    
    total_found = 0
    
    for feed_url in FEEDS:
        print(f"\n--- Checking Feed: {feed_url} ---")
        try:
            # Some feeds require a User-Agent
            d = feedparser.parse(feed_url, agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            if d.bozo:
                print(f"  ! Feed Error (Bozo): {d.bozo_exception}")
            
            if not d.entries:
                print("  ! No entries found in feed.")
                continue
                
            print(f"  Found {len(d.entries)} entries. Checking first 5...")
            
            for i, entry in enumerate(d.entries[:5]):
                title = entry.get('title', 'No Title')
                published = entry.get('published', 'No published string')
                published_parsed = entry.get('published_parsed')
                updated_parsed = entry.get('updated_parsed')
                
                print(f"    [{i+1}] {title[:40]}...")
                print(f"        Raw Date: {published}")
                
                date_struct = published_parsed or updated_parsed
                if not date_struct:
                    print("        ! SKIPPED: No parsed date found.")
                    continue
                    
                published_dt = datetime(*date_struct[:6])
                print(f"        Parsed UTC: {published_dt}")
                
                if published_dt >= cutoff_time:
                    print("        -> STATUS: ACCEPTED")
                    total_found += 1
                else:
                    print("        -> STATUS: REJECTED (Too old)")
                    
        except Exception as e:
            print(f"  ! Exception: {e}")

    print(f"\nTotal Accepted Articles: {total_found}")

if __name__ == "__main__":
    debug_feeds()
