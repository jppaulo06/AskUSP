SELECT ai.create_vectorizer(
    'public.jornal_da_usp_articles'::regclass, 
    destination => 'jornal_da_usp_articles_embedding_oai_small_v3'
  , embedding=>ai.embedding_openai('text-embedding-3-small', 1536, api_key_name=>'OPENAI_API_KEY')
  , chunking=>ai.chunking_recursive_character_text_splitter(
        'content',
        chunk_size => 2000,
	chunk_overlap => 500
    )
  , formatting=>ai.formatting_python_template('Título: $title, Autor: $author, Data (AA/MM/DD): $date, Url: $url, Chunk: $chunk')
);

SELECT ai.create_vectorizer(
    'public.answers_cache'::regclass, 
    destination => 'answers_cache_embedding_oai_small_v3'
  , embedding=>ai.embedding_openai('text-embedding-3-small', 1536, api_key_name=>'OPENAI_API_KEY')
  , chunking=>ai.chunking_recursive_character_text_splitter(
        'question',
        chunk_size => 2000,
        chunk_overlap => 500
    )
);
