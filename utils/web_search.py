import os
import time
import serpapi
from dotenv import load_dotenv
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from crawl4ai.models import CrawlResult
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

load_dotenv("../")

SERP_API_KEY = os.getenv("SERP_API_KEY")

def ensure_url_protocol(urls: list[str]) -> list[str]:
    normalized_urls = []
    for url in urls:
        if url.startswith('Failed to fetch'):
            continue
            
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            if url.startswith('www.'):
                normalized_urls.append(f"https://{url}")
            elif not url.startswith(('http://', 'https://')):
                normalized_urls.append(f"https://{url}")
            else:
                normalized_urls.append(url)
        else:
            normalized_urls.append(url)
    return normalized_urls


def check_robots_txt(urls: list[str]) -> list[str]:
    allowed_urls = []
    normalized_urls = ensure_url_protocol(urls)
    
    for url in normalized_urls:
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            rp = RobotFileParser(robots_url)
            rp.read()

            if rp.can_fetch("*", url):
                allowed_urls.append(url)
            else:
                print(f"Blocked by robots.txt: {url}")

        except Exception as e:
            print(f"Error checking robots.txt for {url}: {e}")
            allowed_urls.append(url)

    return allowed_urls

async def crawl_webpages(urls: list[str], prompt: str) -> CrawlResult:
    # Ensure all URLs are properly formatted before crawling
    urls = ensure_url_protocol(urls)
    
    # Filter out any invalid URLs
    valid_urls = [url for url in urls if url.startswith(('http://', 'https://'))]
    
    if not valid_urls:
        raise ValueError("No valid URLs to crawl")
    
    bm25_filter = BM25ContentFilter(user_query=prompt, bm25_threshold=1.2)
    md_generator = DefaultMarkdownGenerator(content_filter=bm25_filter)

    crawler_config = CrawlerRunConfig(
        markdown_generator=md_generator,
        excluded_tags=["nav", "footer", "header", "form", "img", "a"],
        only_text=True,
        exclude_social_media_links=True,
        keep_data_attributes=False,
        cache_mode=CacheMode.BYPASS,
        remove_overlay_elements=True,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        page_timeout=60000,  # in ms: 60 seconds
    )
    browser_config = BrowserConfig(headless=True, text_mode=True, light_mode=True)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(valid_urls, config=crawler_config)
        return results


def get_web_urls(search_term: str, num_results: int = 5) -> list[str]:
    try:
        time.sleep(1)

        client = serpapi.Client(api_key=SERP_API_KEY)

        discard_sites = ["youtube.com", "britannica.com", "vimeo.com", "wikipedia.org", "ycombinator.com"]
        for site in discard_sites:
            search_term += f" -site:{site}"

        params = {
            "engine": "google",
            "q": search_term,
            "google_domain": "google.com",
            "gl": "us",   # -> pe
            "hl": "en",  # -> es
            "num": num_results,
            "api_key": SERP_API_KEY
        }
        params["start"] = 10 

        results = client.search(**params)

        if "error" in results:
            print(f"SerpAPI error: {results['error']}")
            return []

        # Extract URLs from organic results
        urls = []
        organic_results = results.get("organic_results", [])
        for res in organic_results:
            if "link" in res:
                urls.append(res["link"])

        # Fallback: if no organic results found, check news_results or related_questions
        if not urls:
            for alt_section in ["news_results", "related_questions"]:
                for item in results.get(alt_section, []):
                    link = item.get("link")
                    if link:
                        urls.append(link)

        # Limit to requested number
        urls = urls[:num_results]

        # Check robots.txt compliance
        allowed_urls = check_robots_txt(urls)

        return allowed_urls

    except Exception as e:
        print(f"Failed to fetch results from SerpAPI: {e}")
        return []
