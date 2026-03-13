"""
GNews API client for fetching real-time news articles
"""

import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class GNewsClient:
    """Client for GNews API"""

    def __init__(self):
        """Initialize GNews client"""
        self.api_key = os.getenv("GNEWS_API_KEY")
        self.base_url = os.getenv("GNEWS_API_URL", "https://gnews.io/api/v4")

        if not self.api_key:
            raise ValueError(
                "GNEWS_API_KEY must be set in environment variables")

    def search_news(
        self,
        query: str = "politics",
        lang: str = "en",
        country: Optional[str] = None,
        max_results: int = 10,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for news articles

        Args:
            query: Search query
            lang: Language code (default: en)
            country: Country code (optional)
            max_results: Maximum number of results (max 100 for free tier)
            from_date: Start date for articles
            to_date: End date for articles

        Returns:
            List of article dictionaries
        """
        endpoint = f"{self.base_url}/search"

        params = {
            "q": query,
            "lang": lang,
            "max": min(max_results, 100),  # Free tier limit
            "apikey": self.api_key
        }

        if country:
            params["country"] = country

        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            return self._format_articles(data.get("articles", []))

        except requests.exceptions.RequestException as e:
            print(f"Error fetching news: {str(e)}")
            return []

    def get_top_headlines(
        self,
        category: Optional[str] = None,
        lang: str = "en",
        country: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top headlines

        Args:
            category: News category (general, world, nation, business, 
                     technology, entertainment, sports, science, health)
            lang: Language code
            country: Country code
            max_results: Maximum number of results

        Returns:
            List of article dictionaries
        """
        endpoint = f"{self.base_url}/top-headlines"

        params = {
            "lang": lang,
            "max": min(max_results, 100),
            "apikey": self.api_key
        }

        if category:
            params["category"] = category

        if country:
            params["country"] = country

        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            return self._format_articles(data.get("articles", []))

        except requests.exceptions.RequestException as e:
            print(f"Error fetching headlines: {str(e)}")
            return []

    def _format_articles(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        """
        Format articles to standardized structure

        Args:
            articles: Raw articles from API

        Returns:
            Formatted articles
        """
        formatted = []

        for article in articles:
            formatted.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", ""),
                "url": article.get("url", ""),
                "image": article.get("image", ""),
                "published_at": article.get("publishedAt", ""),
                "source": article.get("source", {}).get("name", ""),
                "source_url": article.get("source", {}).get("url", "")
            })

        return formatted

    def get_recent_news_for_analysis(
        self,
        topics: List[str] = ["politics", "breaking news", "world news"],
        max_per_topic: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent news articles for fake news analysis

        Args:
            topics: List of topics to search
            max_per_topic: Maximum articles per topic

        Returns:
            Combined list of articles
        """
        all_articles = []
        seen_urls = set()

        for topic in topics:
            articles = self.search_news(
                query=topic,
                max_results=max_per_topic,
                from_date=datetime.now() - timedelta(days=1)
            )

            # Deduplicate by URL
            for article in articles:
                url = article.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_articles.append(article)

        return all_articles


# Global instance
_gnews_client: Optional[GNewsClient] = None


def get_gnews_client() -> GNewsClient:
    """Get or create GNews client instance"""
    global _gnews_client
    if _gnews_client is None:
        _gnews_client = GNewsClient()
    return _gnews_client
