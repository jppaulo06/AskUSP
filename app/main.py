from config.settings import get_settings
from loguru import logger
import asyncio
import pandas as pd
from config.settings import get_settings
import psycopg2
from psycopg2.extensions import connection as PostgresConnection
from .models.synthesizer import Synthesizer
from datetime import datetime

settings = get_settings()


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

Responda à pergunta do usuário:
"""


def semantic_search(
    conn: PostgresConnection, query_text: str, limit: int = 15
) -> pd.DataFrame:
    with conn.cursor() as cursor:
        search_query = """
            SELECT 
            chunk,
            to_char(date, 'DD/MM/YYYY'),
            url,
            author,
            title
            FROM jornal_da_usp_articles_embedding_oai_small_v3
            ORDER BY embedding <=> (
                SELECT ai.openai_embed('text-embedding-3-small', %s)
            )
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
    synthesizer = Synthesizer(settings.openai, SYSTEM_PROMPT)
    conn: PostgresConnection = psycopg2.connect(settings.postgres.url)

    question = "Quais são as notícias recentes da USP, considerando que hoje é 8 de fevereiro de 2025?"
    search = f"""
    Dia e hora da pergunta: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    Pergunta do usuário: {question}
    """
    context = semantic_search(conn, search)

    for i, row in context.iterrows():
        logger.info(f"Conteúdo: {row['Conteúdo']}")
        logger.info(f"Data de Publicação: {row['Data de Publicação']}")
        logger.info(f"URL: {row['URL']}")
        logger.info(f"Autor: {row['Autor']}")
        logger.info(f"Título: {row['Título']}")
        logger.info("\n")

    response = await synthesizer.generate_response(question, context)
    logger.debug(response)

    if response.enough_context:
        logger.info(f"Answer: {response.answer}")
    else:
        logger.info("Insufficient context to answer the question.")
        logger.info("Thought process:")
        for thought in response.thought_process:
            logger.info(thought)

    conn.close()


if __name__ == "__main__":
    asyncio.run(main())
