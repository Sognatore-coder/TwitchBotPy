# Игровые новости с PC Gamer через Google News RSS
import random
import requests
import xml.etree.ElementTree as ET
from translator import translate
 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
 
RSS_QUERIES = [
    "gaming news 2026 site:pcgamer.com",
    "new game release 2026 site:pcgamer.com",
    "game update 2026 site:pcgamer.com",
    "PC game review 2026 site:pcgamer.com",
]
 
_shown_urls: set[str] = set()
 
 
def _fetch_rss(query: str) -> list[dict]:
    url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall(".//item"):
            title_el = item.find("title")
            link_el  = item.find("link")
            date_el  = item.find("pubDate")
            if title_el is None or link_el is None:
                continue
            items.append({
                "title": title_el.text or "",
                "url":   link_el.text or "",
                "date":  (date_el.text or "")[:16] if date_el is not None else "",
            })
        return items
    except Exception:
        return []
 
 
def _resolve_url(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        return r.url
    except Exception:
        return url
 
 
GAMING_KEYWORDS = [
    "game", "gaming", "update", "patch", "dlc", "release", "steam",
    "studio", "developer", "playstation", "xbox", "nintendo", "fps",
    "rpg", "mmo", "esports", "mod", "review", "trailer", "launch",
]
 
 
def _collect_articles() -> list[dict]:
    seen = set()
    result = []
    for query in RSS_QUERIES:
        for art in _fetch_rss(query):
            low = art["title"].lower()
            is_gaming = any(kw in low for kw in GAMING_KEYWORDS)
            if art["url"] not in seen and "2026" in art["date"] and is_gaming:
                seen.add(art["url"])
                result.append(art)
    return result
 
 
def gaming_news() -> str:
    global _shown_urls
    try:
        articles = _collect_articles()
        if not articles:
            return "Свежие игровые новости не найдены."
 
        fresh = [a for a in articles if a["url"] not in _shown_urls]
        if not fresh:
            _shown_urls.clear()
            fresh = articles
 
        article = random.choice(fresh)
        _shown_urls.add(article["url"])
 
        title    = translate(article["title"])
        real_url = _resolve_url(article["url"])
        date     = article["date"]
 
        return (
            f"📰 *{title}*\n"
            f"📅 {date}\n\n"
            f"🔗 [Читать на PC Gamer]({real_url})"
        )
 
    except Exception as e:
        return f"Ошибка получения новостей: {e}"