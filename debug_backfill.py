import asyncio
from backend.database import get_backfill_candidates

async def test_backfill():
    print("Testing get_backfill_candidates...")
    candidates = await get_backfill_candidates(limit=10)
    print(f"Found {len(candidates)} candidates.")
    for c in candidates:
        print(f"- {c.get('headline')} (Status: {c.get('processing_status')}, Keywords: {len(c.get('keywords', []))})")

if __name__ == "__main__":
    asyncio.run(test_backfill())
