import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
)
from pydantic import BaseModel
from lib import get_urls, crawl_parallel
from loguru import logger


class JornalDaUspArticle(BaseModel):
    title: str
    content: str
    author: str
    url: str
    date: str


async def get_jornal_da_usp_article(page_markdown: str, url: str) -> JornalDaUspArticle:
    # Usually there are import stuff before the article
    extra_markdown = page_markdown.split("Publicado")[0].split("##")[-1]
    extra_splited = extra_markdown.splitlines()
    title = extra_splited[0].strip()
    try:
        author = extra_splited[1].split("Por ")[1].split(",")[0].strip()
    except IndexError:
        author = ""

    # The article is usually between "Publicado" (which tells the date) and "_______________"
    article_markdown = page_markdown.split("Publicado")[1].split("Política de uso")[0]
    article_splited = article_markdown.splitlines()
    date = article_splited[0].split(": ")[1].strip()
    content = "\n".join(article_splited[3:])

    return JornalDaUspArticle(
        title=title,
        content=content,
        author=author,
        url=url,
        date=date,
    )


async def crawl_jornal_da_usp_article(
    url: str,
    crawler: AsyncWebCrawler,
    crawl_config: CrawlerRunConfig,
    session_id: str,
    verbose: bool = False,
) -> JornalDaUspArticle:
    crawl_result = await crawler.arun(
        url=url,
        crawl_config=crawl_config,
        session_id=session_id,
        verbose=verbose,
    )
    if crawl_result.success:
        assert isinstance(crawl_result.markdown, str)
        if verbose:
            logger.debug(crawl_result.markdown)
        article = await get_jornal_da_usp_article(crawl_result.markdown, url)
        return article
    else:
        raise Exception(f"Error crawling {url}: {crawl_result}")


async def dev():
    crawler = AsyncWebCrawler()
    await crawler.start()
    crawl_config = CrawlerRunConfig(disable_cache=True)
    session_id = "jornal-da-usp"
    article = await crawl_jornal_da_usp_article(
        "https://jornal.usp.br/articulistas/jose-roberto-castilho-piqueira/maneiras-de-olhar-e-pensar/",
        crawler,
        crawl_config,
        session_id,
        verbose=True,
    )
    logger.info(article)
    await crawler.close()


async def main():
    urls = get_urls("https://jornal.usp.br/post-sitemap.xml")
    await crawl_parallel(urls, crawl_jornal_da_usp_article, max_concurrent=10)


if __name__ == "__main__":
    asyncio.run(main())
