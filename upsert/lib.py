from typing import Callable
from pydantic import BaseModel
from loguru import logger
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import psutil
import os
import asyncio
from typing import Coroutine
from xml.etree import ElementTree
from functools import reduce
import requests


def _memory_in_mb(memory: int) -> int:
    return memory // (1024 * 1024)


@logger.catch(reraise=True)
def get_urls(sitemap_url: str) -> list[str]:
    response = requests.get(sitemap_url)
    response.raise_for_status()
    if response.status_code != 200:
        raise Exception("Failed to get sitemap")
    root = ElementTree.fromstring(response.content)
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = root.findall(".//ns:loc", namespace)
    urls: list[str] = reduce(
        lambda acc, loc: acc + [loc.text] if isinstance(loc.text, str) else [],
        locs,
        [],
    )
    return urls


@logger.catch(reraise=True)
async def crawl_parallel(
    urls: list[str],
    crawl_func: Callable[
        [str, AsyncWebCrawler, CrawlerRunConfig, str], Coroutine[None, None, BaseModel]
    ],
    max_concurrent: int = 3,
):
    peak_memory = 0
    process = psutil.Process(os.getpid())

    def log_memory(prefix: str = "") -> None:
        nonlocal peak_memory
        current_mem = _memory_in_mb(process.memory_info().rss)
        peak_memory = max(current_mem, peak_memory)
        logger.debug(
            f"{prefix} Current Memory: {current_mem} MB, Peak: {peak_memory // (1024 * 1024)} MB"
        )

    # Minimal browser config
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    # Create the crawler instance
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    success_count = 0
    fail_count = 0

    try:
        # Chunk the URLs in batches of 'max_concurrent'
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            tasks = []

            for j, url in enumerate(batch):
                # Unique session_id per concurrent sub-task
                session_id = f"parallel_session_{i}_{j}"
                task = crawl_func(url, crawler, crawl_config, session_id)
                tasks.append(task)

            log_memory(prefix=f"Before batch {i//max_concurrent + 1}: ")
            results: list[BaseException | BaseModel] = await asyncio.gather(
                *tasks, return_exceptions=True
            )
            log_memory(prefix=f"After batch {i//max_concurrent + 1}: ")

            for url, result in zip(batch, results):
                if isinstance(result, BaseException):
                    logger.error(f"Error crawling {url}: {result}")
                    fail_count += 1
                else:
                    logger.info(f"Success crawling {url}: {result}")
                    success_count += 1
    finally:
        await crawler.close()
        log_memory("After closing crawler: ")
        logger.info(
            f"Peak Memory Usage: {peak_memory} MB\n"
            f"Success: {success_count}, Fail: {fail_count}"
        )
