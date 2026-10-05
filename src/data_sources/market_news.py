from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
import re
from urllib.parse import quote, urljoin, urlparse
from xml.etree import ElementTree

import pandas as pd
import requests
import streamlit as st


NEWS_CATEGORIES = (
    "宏观经济", "美联储", "中国货币政策", "政治", "行业", "市场", "Crypto",
)
GOOGLE_NEWS_SEARCHES = (
    (
        "宏观经济",
        "global economy inflation central bank GDP interest rates",
        "en-US", "US",
    ),
    (
        "美联储",
        "Federal Reserve FOMC interest rate monetary policy",
        "en-US", "US",
    ),
    (
        "中国货币政策",
        "中国人民银行 货币政策 LPR 降准 利率",
        "zh-CN", "CN",
    ),
    (
        "政治",
        "geopolitics government policy trade sanctions markets",
        "en-US", "US",
    ),
    (
        "行业",
        "industry AI semiconductor energy automotive business",
        "en-US", "US",
    ),
    (
        "市场",
        "global stock markets bonds commodities currencies",
        "en-US", "US",
    ),
    (
        "Crypto",
        "cryptocurrency Bitcoin Ethereum digital assets",
        "en-US", "US",
    ),
)
RSS_FEEDS = (
    ("美联储", "美联储（官网）", "https://www.federalreserve.gov/feeds/press_all.xml"),
    ("市场", "CNBC", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("市场", "MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/"),
)
OFFICIAL_LISTINGS = (
    (
        "中国货币政策",
        "中国人民银行（官网）",
        "https://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html",
    ),
    (
        "宏观经济",
        "国家统计局（官网）",
        "https://www.stats.gov.cn/sj/zxfb/",
    ),
)
NEWS_PROVIDERS = (
    "Google News", "CNBC", "MarketWatch", "美联储（官网）",
    "中国人民银行（官网）", "国家统计局（官网）",
)
NEWS_COLUMNS = [
    "categories", "title", "publisher", "provider", "published_at", "url",
    "related_tickers",
]


class _ArticleLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_anchor = False
        self._href = ""
        self._text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._in_anchor = True
            self._href = dict(attrs).get("href") or ""
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._in_anchor and data.strip():
            self._text.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_anchor:
            title = " ".join(self._text).strip()
            if title and self._href:
                self.links.append((title, self._href))
            self._in_anchor = False


def _parse_rss_items(content: bytes, provider: str, category: str) -> list[dict]:
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise ValueError(f"{provider} RSS 格式无效") from exc

    rows = []
    for item in root.findall(".//item"):
        title = item.findtext("title")
        url = item.findtext("link")
        published_text = item.findtext("pubDate")
        source_element = item.find("source")
        publisher = (
            source_element.text.strip()
            if source_element is not None and source_element.text
            else provider
        )
        if not title or not url or not published_text:
            continue
        try:
            published_at = parsedate_to_datetime(published_text)
        except (TypeError, ValueError, OverflowError):
            continue
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        rows.append({
            "categories": [category],
            "title": title.strip(),
            "publisher": publisher,
            "provider": provider,
            "published_at": published_at.astimezone(timezone.utc),
            "url": url.strip(),
            "related_tickers": "",
        })
    return rows


def _fetch_google_news(
    category: str, query: str, language: str, region: str
) -> list[dict]:
    url = (
        "https://news.google.com/rss/search?q="
        f"{quote(query)}&hl={language}&gl={region}&ceid={region}:{language.split('-')[0]}"
    )
    response = requests.get(
        url, timeout=12, headers={"User-Agent": "Mozilla/5.0"}
    )
    response.raise_for_status()
    return _parse_rss_items(response.content, "Google News", category)


def _fetch_rss_feed(category: str, provider: str, url: str) -> list[dict]:
    response = requests.get(
        url, timeout=12, headers={"User-Agent": "Mozilla/5.0"}
    )
    response.raise_for_status()
    return _parse_rss_items(response.content, provider, category)


def _fetch_official_listing(category: str, provider: str, url: str) -> list[dict]:
    response = requests.get(
        url, timeout=12, headers={"User-Agent": "Mozilla/5.0"}
    )
    response.raise_for_status()
    parser = _ArticleLinks()
    encoding = response.apparent_encoding or response.encoding or "utf-8"
    parser.feed(response.content.decode(encoding, errors="replace"))

    rows: list[dict] = []
    for title, href in parser.links:
        article_url = urljoin(url, href)
        parsed = urlparse(article_url)
        date_match = re.search(r"(20\d{6})", parsed.path)
        if date_match is None or parsed.scheme != "https" or not parsed.netloc:
            continue
        try:
            published_at = datetime.strptime(date_match.group(1), "%Y%m%d").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            continue
        rows.append({
            "categories": [category],
            "title": title,
            "publisher": provider.removesuffix("（官网）"),
            "provider": provider,
            "published_at": published_at,
            "url": article_url,
            "related_tickers": "",
        })
    return rows


@st.cache_data(ttl=600, max_entries=1)
def fetch_market_news() -> tuple[pd.DataFrame, list[str], datetime]:
    """Fetch categorized headlines from news media and official policy sources."""
    jobs = [
        (
            category,
            f"Google News（{category}）",
            _fetch_google_news,
            (category, query, language, region),
        )
        for category, query, language, region in GOOGLE_NEWS_SEARCHES
    ]
    jobs.extend(
        (
            category,
            provider,
            _fetch_rss_feed,
            (category, provider, url),
        )
        for category, provider, url in RSS_FEEDS
    )
    jobs.extend(
        (
            category,
            provider,
            _fetch_official_listing,
            (category, provider, url),
        )
        for category, provider, url in OFFICIAL_LISTINGS
    )

    results: list[dict] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
        futures = {
            executor.submit(fetcher, *args): label
            for _, label, fetcher, args in jobs
        }
        for future in as_completed(futures):
            label = futures[future]
            try:
                results.extend(future.result())
            except (requests.RequestException, ValueError) as exc:
                errors.append(f"{label}：{exc}")

    now = datetime.now(timezone.utc)
    by_url: dict[str, dict] = {}
    for article in results:
        url = article["url"]
        try:
            parsed_url = urlparse(url)
        except ValueError:
            continue
        if (
            parsed_url.scheme != "https"
            or not parsed_url.netloc
            or article["published_at"] > now
            or now - article["published_at"] > timedelta(days=7)
        ):
            continue
        existing = by_url.get(url)
        if existing is None:
            by_url[url] = article
        else:
            existing["categories"] = list(dict.fromkeys(
                existing["categories"] + article["categories"]
            ))

    headlines = pd.DataFrame(by_url.values(), columns=NEWS_COLUMNS)
    if not headlines.empty:
        headlines = headlines.sort_values(
            "published_at", ascending=False
        ).reset_index(drop=True)
    errors.sort()
    return headlines, errors, now
