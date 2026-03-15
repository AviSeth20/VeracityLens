import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class GNewsClient:
    def __init__(self):
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
        to_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Search for news articles by query."""
        params = {
            "q": query,
            "lang": lang,
            "max": min(max_results, 100),
            "apikey": self.api_key,
        }
        if country:
            params["country"] = country
        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            response = requests.get(
                f"{self.base_url}/search", params=params, timeout=10)
            response.raise_for_status()
            return self._format_articles(response.json().get("articles", []))
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news: {e}")
            return []

    def get_top_headlines(
        self,
        category: Optional[str] = None,
        lang: str = "en",
        country: Optional[str] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get top headlines, optionally filtered by category."""
        params = {
            "lang": lang,
            "max": min(max_results, 100),
            "apikey": self.api_key,
        }
        if category:
            params["category"] = category
        if country:
            params["country"] = country

        try:
            response = requests.get(
                f"{self.base_url}/top-headlines", params=params, timeout=10)
            response.raise_for_status()
            return self._format_articles(response.json().get("articles", []))
        except requests.exceptions.RequestException as e:
            print(f"Error fetching headlines: {e}")
            return []

    def _format_articles(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        return [
            {
                "title":       article.get("title", ""),
                "description": article.get("description", ""),
                "content":     article.get("content", ""),
                "url":         article.get("url", ""),
                "image":       article.get("image", ""),
                "published_at": article.get("publishedAt", ""),
                "source":      article.get("source", {}).get("name", ""),
                "source_url":  article.get("source", {}).get("url", ""),
            }
            for article in articles
        ]

    def get_recent_news_for_analysis(
        self,
        topics: List[str] = ["politics", "breaking news", "world news"],
        max_per_topic: int = 5,
    ) -> List[Dict[str, Any]]:
        """Fetch and deduplicate articles across multiple topics."""
        all_articles = []
        seen_urls: set = set()
        for topic in topics:
            articles = self.search_news(
                query=topic,
                max_results=max_per_topic,
                from_date=datetime.now() - timedelta(days=1),
            )
            for article in articles:
                url = article.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_articles.append(article)
        return all_articles


_gnews_client: Optional[GNewsClient] = None


def get_gnews_client() -> GNewsClient:
    global _gnews_client
    if _gnews_client is None:
        _gnews_client = GNewsClient()
    return _gnews_client
