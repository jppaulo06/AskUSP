import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
)
from pydantic import BaseModel
from loguru import logger
from datetime import datetime
import psycopg2
from config.settings import get_settings
from .lib import get_urls, upsert_parallel
from psycopg2.extensions import connection as PostgresConnection


class JornalDaUspArticle(BaseModel):
    title: str
    content: str
    author: str
    url: str
    date: datetime


settings = get_settings()


async def get_jornal_da_usp_article(page_markdown: str, url: str) -> JornalDaUspArticle:
    # Usually there are import stuff before the article
    extra_markdown = page_markdown.split("Publicado")[0].split("##")[-1]
    extra_splited = extra_markdown.splitlines()
    title = extra_splited[0].strip()
    try:
        author = extra_splited[1].split("Por ")[1].split(",")[0].strip()
    except IndexError:
        author = "Jornal da USP"

    article_markdown = page_markdown.split("Publicado")[1].split("Política de uso")[0]
    article_splited = article_markdown.splitlines()
    content = "\n".join(article_splited[3:])
    date_str = article_splited[0].split(": ")[1].strip()
    date = datetime.strptime(date_str, "%d/%m/%Y às %H:%M")

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


async def upsert_jornal_da_usp_article(
    db_conn: PostgresConnection,
    article: JornalDaUspArticle,
) -> None:
    logger.info(f"Upserting article {article.title} from {article.author}")
    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO jornal_da_usp_articles (title, content, author, url, date)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                article.title,
                article.content,
                article.author,
                article.url,
                article.date,
            ),
        )
        try:
            db_conn.commit()
        except Exception as e:
            db_conn.rollback()
            raise RuntimeError(f"Error upserting article {article.title}: {e}")


async def dev():
    crawler = AsyncWebCrawler()
    await crawler.start()
    crawl_config = CrawlerRunConfig(disable_cache=True)
    session_id = "jornal-da-usp"
    article = await crawl_jornal_da_usp_article(
        "https://jornal.usp.br/comunicados/usp-aprimora-ensino-da-odontologia-com-novos-laboratorios-e-espaco-sensorial-na-fo/",
        crawler,
        crawl_config,
        session_id,
        verbose=True,
    )
    logger.info(article)
    await crawler.close()


async def main():
    urls = get_urls("https://jornal.usp.br/post-sitemap.xml")[:15]
    with psycopg2.connect(settings.postgres.url) as db_conn:
        await upsert_parallel(
            db_conn,
            crawl_func=crawl_jornal_da_usp_article,
            upsert_func=upsert_jornal_da_usp_article,
            urls=urls,
            max_concurrent=3,
        )


if __name__ == "__main__":
    asyncio.run(dev())
