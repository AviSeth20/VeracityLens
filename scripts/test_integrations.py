"""
Test script for Supabase and GNews API integrations
"""

import asyncio
from datetime import datetime
from src.utils.gnews_client import get_gnews_client
from src.utils.supabase_client import get_supabase_client
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_supabase_connection():
    """Test Supabase connection and basic operations"""
    print("\n" + "="*60)
    print("TESTING SUPABASE CONNECTION")
    print("="*60)

    try:
        client = get_supabase_client()
        print("✅ Supabase client initialized successfully")
        print(f"   URL: {client.url}")

        # Test connection by querying predictions table
        response = client.client.table(
            "predictions").select("*").limit(1).execute()
        print(f"✅ Successfully connected to Supabase database")
        print(f"   Predictions table accessible")

        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {str(e)}")
        return False


def test_gnews_api():
    """Test GNews API connection"""
    print("\n" + "="*60)
    print("TESTING GNEWS API")
    print("="*60)

    try:
        client = get_gnews_client()
        print("✅ GNews client initialized successfully")

        # Fetch top headlines
        print("\nFetching top headlines...")
        articles = client.get_top_headlines(max_results=3)

        if articles:
            print(f"✅ Successfully fetched {len(articles)} articles")
            print("\nSample articles:")
            for i, article in enumerate(articles[:3], 1):
                print(f"\n{i}. {article['title']}")
                print(f"   Source: {article['source']}")
                print(f"   Published: {article['published_at']}")
                print(f"   URL: {article['url'][:60]}...")
        else:
            print("⚠️  No articles returned (check API key and quota)")

        return True
    except Exception as e:
        print(f"❌ GNews API test failed: {str(e)}")
        return False


async def test_supabase_operations():
    """Test Supabase CRUD operations"""
    print("\n" + "="*60)
    print("TESTING SUPABASE OPERATIONS")
    print("="*60)

    try:
        client = get_supabase_client()

        # Test storing a prediction
        print("\n[1/3] Testing prediction storage...")
        test_article_id = f"test_{datetime.now().timestamp()}"

        await client.store_prediction(
            article_id=test_article_id,
            text="This is a test article for integration testing.",
            predicted_label="True",
            confidence=0.95,
            model_name="distilbert",
            explanation={"top_words": ["test", "article"]}
        )
        print("✅ Prediction stored successfully")

        # Test storing feedback
        print("\n[2/3] Testing feedback storage...")
        await client.store_feedback(
            article_id=test_article_id,
            predicted_label="True",
            actual_label="Fake",
            user_comment="This was actually fake news"
        )
        print("✅ Feedback stored successfully")

        # Test retrieving stats
        print("\n[3/3] Testing statistics retrieval...")
        stats = await client.get_prediction_stats()
        print(f"✅ Statistics retrieved successfully")
        print(f"   Total predictions: {stats['total_predictions']}")
        print(f"   By label: {stats['by_label']}")

        return True
    except Exception as e:
        print(f"❌ Supabase operations test failed: {str(e)}")
        return False


def test_gnews_search():
    """Test GNews search functionality"""
    print("\n" + "="*60)
    print("TESTING GNEWS SEARCH")
    print("="*60)

    try:
        client = get_gnews_client()

        # Test search
        print("\nSearching for 'politics' news...")
        articles = client.search_news(query="politics", max_results=3)

        if articles:
            print(f"✅ Found {len(articles)} articles")
            for i, article in enumerate(articles, 1):
                print(f"\n{i}. {article['title'][:80]}...")
        else:
            print("⚠️  No articles found")

        # Test recent news for analysis
        print("\n\nFetching recent news for analysis...")
        recent = client.get_recent_news_for_analysis(
            topics=["breaking news"],
            max_per_topic=2
        )
        print(f"✅ Retrieved {len(recent)} recent articles")

        return True
    except Exception as e:
        print(f"❌ GNews search test failed: {str(e)}")
        return False


def main():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("FAKE NEWS DETECTION - INTEGRATION TESTS")
    print("="*60)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {
        "Supabase Connection": test_supabase_connection(),
        "GNews API": test_gnews_api(),
        "GNews Search": test_gnews_search(),
    }

    # Run async tests
    print("\nRunning async tests...")
    try:
        loop = asyncio.get_event_loop()
        results["Supabase Operations"] = loop.run_until_complete(
            test_supabase_operations()
        )
    except Exception as e:
        print(f"❌ Async tests failed: {str(e)}")
        results["Supabase Operations"] = False

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:30} {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All integration tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check configuration:")
        print("   1. Ensure .env file exists with correct credentials")
        print("   2. Run setup_supabase.sql in Supabase SQL Editor")
        print("   3. Verify API keys are valid")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
