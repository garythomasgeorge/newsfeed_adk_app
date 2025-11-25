import asyncio
from backend.agents import NewsChiefAgent, HarvesterAgent, AnalystAgent, LibrarianAgent

# Mock feeds
MOCK_FEEDS = {
    "Test": ["http://test.com/rss"]
}

def test_adk_agents():
    """Test that all ADK agents can be instantiated correctly."""
    print("Testing ADK Agent Instantiation...")
    
    # 1. Initialize Agents
    harvester = HarvesterAgent(feeds=MOCK_FEEDS)
    print(f"✓ HarvesterAgent created: {harvester.name}")
    
    analyst = AnalystAgent()
    print(f"✓ AnalystAgent created: {analyst.name}")
    
    librarian = LibrarianAgent()
    print(f"✓ LibrarianAgent created: {librarian.name}")
    
    chief = NewsChiefAgent(harvester, analyst)
    print(f"✓ NewsChiefAgent created: {chief.name}")
    
    # 2. Verify agent properties
    assert harvester.name == "Harvester"
    assert analyst.name == "Analyst"
    assert librarian.name == "Librarian"
    assert chief.name == "NewsChief"
    
    print("\n✅ All tests passed! ADK agents are properly configured.")
    print("\nAgent Details:")
    print(f"  - {harvester.name}: {harvester.model}")
    print(f"  - {analyst.name}: {analyst.model}")
    print(f"  - {librarian.name}: {librarian.model}")
    print(f"  - {chief.name}: {chief.model}")

if __name__ == "__main__":
    test_adk_agents()
