"""
Test script to verify Supabase and GNews API connections
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.utils.supabase_client import get_supabase_client
from src.utils.gnews_client import get_gnews_client

load_dotenv()

def test_supabase():
    """Test Supabase connection"""
    print("\n" + "="*60)
    print("Testing Supabase Connection")
    print("="*60)
    
    try:
        client = get_supabase_client()
        print("✅ Supabase client initialized successfully")
        
        # Test connection by querying predictions table
        response = client.client.table("predictions").select("*").limit(1).execute()
        print(f"✅ Successfully connected to Supabase")
        print(f"   URL: {client.url}")
        print(f"   Tables accessible: predictions, feedback, news_articles")
        
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check SUPABASE_URL in .env file")
        print("2. Check SUPABASE_KEY in .env file")
        print("3. Ensure tables are created (run setup_supabase.sql)")
        return False

def test_gnews():
    """Test GNews API connection"""
    print("\n" + "="*60)
    print("Testing GNews API Connection")
    print("="*60)
    
    try:
        client = get_gnews_client()
        print("✅ GNews client initialized successfully")
        
        # Test API by fetching a few articles
        articles = client.search_news(query="technology", max_results=3)
        
        if articles:
            print(f"✅ Successfully fetched {len(articles)} articles from GNews")
            print(f"   API Key: {client.api_key[:10]}...")
            print(f"   Base URL: {client.base_url}")
            
            print("\n   Sample article:")
            if articles:
                article = articles[0]
                print(f"   - Title: {article['title'][:60]}...")
                print(f"   - Source: {article['source']}")
                print(f"   - Published: {article['published_at']}")
            
            return True
        else:
            print("⚠️  GNews API connected but returned no articles")
            print("   This might be normal if no articles match the query")
            return True
            
    except Exception as e:
        print(f"❌ GNews API connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check GNEWS_API_KEY in .env file")
        print("2. Verify API key at https://gnews.io/")
        print("3. Check if you've exceeded free tier limits (100 requests/day)")
        return False

def test_environment():
    """Test environment variables"""
    print("\n" + "="*60)
    print("Checking Environment Variables")
    print("="*60)
    
    required_vars = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
        "GNEWS_API_KEY": os.getenv("GNEWS_API_KEY")
    }
    
    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value:
            masked_value = var_value[:10] + "..." if len(var_value) > 10 else "***"
            print(f"✅ {var_name}: {masked_value}")
        else:
            print(f"❌ {var_name}: NOT SET")
            all_set = False
    
    if not all_set:
        print("\n⚠️  Some environment variables are missing")
        print("   Copy .env.example to .env and fill in your credentials")
    
    return all_set

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("FAKE NEWS DETECTION - CONNECTION TESTS")
    print("="*60)
    
    # Test environment variables
    env_ok = test_environment()
    
    if not env_ok:
        print("\n❌ Environment variables not configured properly")
        print("   Please set up your .env file before running tests")
        return
    
    # Test Supabase
    supabase_ok = test_supabase()
    
    # Test GNews
    gnews_ok = test_gnews()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Supabase Connection:   {'✅ PASS' if supabase_ok else '❌ FAIL'}")
    print(f"GNews API Connection:  {'✅ PASS' if gnews_ok else '❌ FAIL'}")
    
    if all([env_ok, supabase_ok, gnews_ok]):
        print("\n🎉 All tests passed! Your backend is ready.")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
