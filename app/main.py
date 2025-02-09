from config.settings import get_settings
from loguru import logger
import asyncio
import pandas as pd
from config.settings import get_settings
import psycopg2
from psycopg2.extensions import connection as PostgresConnection
from .models.synthesizer import Synthesizer
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

settings = get_settings()


class SynthesizedResponse(BaseModel):
    enough_context: bool = Field(
        description="Whether the assistant has enough context to answer the question"
    )
    answer: str = Field(description="The synthesized answer to the user's question")


SYSTEM_PROMPT = """
# Função
Você é um assistente virtual que fornece informações sobre notícias recentes da USP.

# Guidelines:
1. Responda de forma clara e concisa à pergunta.
2. Forneça informações precisas e atualizadas sobre notícias recentes da USP.
3. O contexto é recuperado com base na similaridade de cosseno, portanto, algumas informações podem estar ausentes ou irrelevantes.
4. Seja transparente quando houver informações insuficientes para responder completamente à pergunta.
5. Não invente ou infira informações não presentes no contexto fornecido.
6. Se não puder responder à pergunta com base no contexto fornecido, declare claramente isso.
7. Mantenha um tom útil e profissional apropriado para o atendimento ao cliente.
8. Indique as fontes de onde as informações foram extraídas, apontando pelo menos a url da notícia.
9. Escreva em português claro e correto, utilizando Markdown.

Responda à pergunta do usuário:
"""


def cache_answer(conn: PostgresConnection, question: str, answer: str) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO answers_cache (question, answer)
            VALUES (%s, %s)
            ON CONFLICT (question) DO UPDATE SET answer = EXCLUDED.answer
            """,
            (question, answer),
        )
        conn.commit()
        logger.debug("Answer cached.")


def get_cached_answer(conn: PostgresConnection, question: str) -> Optional[str]:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            WITH query_embedding AS (
                SELECT ai.openai_embed('text-embedding-3-small', %s) AS qe
            )
            SELECT answer
            FROM answers_cache_embedding_oai_small_v3, query_embedding
            WHERE (embedding <=> qe) < 0.2
            ORDER BY embedding <=> qe
            LIMIT 1;
            """,
            (question,),
        )
        result = cursor.fetchone()

        if result:
            logger.debug("Cached answer found.")
            return result[0]

        logger.debug("No cached answer found.")
        return None


def semantic_search(
    conn: PostgresConnection, query_text: str, limit: int = 15
) -> pd.DataFrame:
    with conn.cursor() as cursor:
        search_query = """
            WITH query_embedding AS (
                SELECT ai.openai_embed('text-embedding-3-small', %s) AS qe
            )
            SELECT 
                chunk,
                to_char(date, 'DD/MM/YYYY'),
                url,
                author,
                title
            FROM jornal_da_usp_articles_embedding_oai_small_v3, query_embedding
            WHERE (embedding <=> qe) < 0.4
            ORDER BY embedding <=> qe
            LIMIT %s;
        """
        try:
            cursor.execute(search_query, (query_text, limit))
            result = cursor.fetchall()
            return pd.DataFrame(
                result,
                columns=["Conteúdo", "Data de Publicação", "URL", "Autor", "Título"],
            )

        except psycopg2.Error as e:
            raise RuntimeError(f"Failed to execute similarity search: {str(e)}") from e


async def main():
    synthesizer = Synthesizer(settings.openai, SYSTEM_PROMPT, SynthesizedResponse)
    conn: PostgresConnection = psycopg2.connect(settings.postgres.url)

    question = "O que você pode me dizer sobre a vacinação contra a COVID-19 na USP?"
    search = f"""
    Dia e hora da pergunta: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    Pergunta do usuário: {question}
    """

    cached_answer = get_cached_answer(conn, question)
    if cached_answer:
        logger.info("Cached answer found.")
        logger.info(cached_answer)
        return

    context = semantic_search(conn, search)

    for i, row in context.iterrows():
        logger.info(f"Conteúdo: {row['Conteúdo']}")
        logger.info(f"Data de Publicação: {row['Data de Publicação']}")
        logger.info(f"URL: {row['URL']}")
        logger.info(f"Autor: {row['Autor']}")
        logger.info(f"Título: {row['Título']}")
        logger.info("\n")

    response = None

    async for partial in synthesizer.generate_response(question, context):
        logger.info(f"Partial enough context: {partial.enough_context}")
        logger.info(f"Partial answer: {partial.answer}")
        response = partial

    if response:
        answer = response
        logger.info(f"Final answer: {answer}")
        cache_answer(conn, question, answer.answer)

    conn.close()


if __name__ == "__main__":
    asyncio.run(main())
