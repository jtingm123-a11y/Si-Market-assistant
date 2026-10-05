from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree

import requests

from src.data_sources.market_news import (
    GOOGLE_NEWS_SEARCHES,
    NEWS_CATEGORIES,
    NEWS_PROVIDERS,
    fetch_market_news,
)


class _Response:
    apparent_encoding = "utf-8"

    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        return None


def _rss(title, link, publisher, published_at):
    root = ElementTree.Element("rss")
    channel = ElementTree.SubElement(root, "channel")
    item = ElementTree.SubElement(channel, "item")
    ElementTree.SubElement(item, "title").text = title
    ElementTree.SubElement(item, "link").text = link
    ElementTree.SubElement(item, "pubDate").text = format_datetime(published_at)
    ElementTree.SubElement(item, "source").text = publisher
    return ElementTree.tostring(root)


def _official_listing(title, url):
    root = ElementTree.Element("html")
    anchor = ElementTree.SubElement(root, "a", href=url)
    anchor.text = title
    return ElementTree.tostring(root)


def test_fetch_market_news_merges_topics_and_includes_official_sources(monkeypatch):
    import src.data_sources.market_news as market_news

    market_news.fetch_market_news.clear()
    now = datetime.now(timezone.utc)
    recent = now - timedelta(hours=1)
    stale = now - timedelta(days=8)
    shared_url = "https://example.com/shared"
    pbc_url = (
        "https://www.pbc.gov.cn/goutongjiaoliu/113456/113469/"
        "2026100510101012345/index.html"
    )
    stats_url = "https://www.stats.gov.cn/sj/zxfb/202610/t20261005_123.html"

    def fake_get(url, params=None, **_kwargs):
        if "news.google.com" in url:
            query = parse_qs(urlparse(url).query)["q"][0]
            category = next(
                category for category, search, _, _ in GOOGLE_NEWS_SEARCHES
                if search == query
            )
            if category == "政治":
                return _Response(_rss("Shared story, second category", shared_url, "Google source", recent))
            if category == "宏观经济":
                return _Response(_rss("Shared story", shared_url, "Google source", recent))
            return _Response(_rss(f"{category} story", f"https://example.com/{category}", "Google source", recent))
        if "federalreserve.gov" in url:
            return _Response(_rss("Fed official release", "https://www.federalreserve.gov/fed.html", "Federal Reserve", recent))
        if "cnbc.com" in url:
            return _Response(_rss("CNBC story", "https://example.com/cnbc", "CNBC", recent))
        if "marketwatch.com" in url:
            return _Response(_rss("Old MarketWatch story", "https://example.com/old", "MarketWatch", stale))
        if "pbc.gov.cn" in url:
            return _Response(_official_listing("人民银行政策发布", pbc_url))
        if "stats.gov.cn" in url:
            return _Response(_official_listing("统计局经济数据", stats_url))
        raise AssertionError(f"Unexpected news URL: {url}")

    monkeypatch.setattr(market_news.requests, "get", fake_get)
    headlines, errors, checked_at = fetch_market_news()
    market_news.fetch_market_news.clear()

    assert not errors
    assert NEWS_CATEGORIES == (
        "宏观经济", "美联储", "中国货币政策", "政治", "行业", "市场", "Crypto",
    )
    assert "中国人民银行（官网）" in NEWS_PROVIDERS
    assert "国家统计局（官网）" in NEWS_PROVIDERS
    shared = headlines.loc[headlines["url"] == shared_url].iloc[0]
    assert set(shared["categories"]) == {"宏观经济", "政治"}
    assert headlines.loc[headlines["url"] == pbc_url].iloc[0]["provider"] == "中国人民银行（官网）"
    assert headlines.loc[headlines["url"] == stats_url].iloc[0]["provider"] == "国家统计局（官网）"
    assert headlines.loc[
        headlines["provider"] == "美联储（官网）", "categories"
    ].iloc[0] == ["美联储"]
    assert "Old MarketWatch story" not in set(headlines["title"])
    assert checked_at.tzinfo == timezone.utc


def test_fetch_market_news_reports_partial_provider_failures(monkeypatch):
    import src.data_sources.market_news as market_news

    market_news.fetch_market_news.clear()

    def fake_get(url, **_kwargs):
        if "cnbc.com" in url:
            raise requests.Timeout("source timed out")
        return _Response(ElementTree.tostring(ElementTree.Element("rss")))

    monkeypatch.setattr(market_news.requests, "get", fake_get)
    headlines, errors, _ = fetch_market_news()
    market_news.fetch_market_news.clear()

    assert headlines.empty
    assert len(errors) == 1
    assert "CNBC" in errors[0]
    assert "source timed out" in errors[0]
