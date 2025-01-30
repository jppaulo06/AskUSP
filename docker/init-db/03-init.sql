SELECT ai.create_vectorizer(
    'public.jornal_da_usp'::regclass, 
    destination => 'jornal_da_usp_embedding_oai_small'
  , embedding=>ai.embedding_openai('text-embedding-3-small', 1536, api_key_name=>'OPENAI_API_KEY')
  , chunking=>ai.chunking_recursive_character_text_splitter('article')
  , formatting=>ai.formatting_python_template('Title: $title, Author: $author, Date: $date, Url: $url, Chunk: $chunk')
);
