CREATE TABLE jornal_da_usp_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    date DATE NOT NULL,
    url TEXT NOT NULL,
    content TEXT NOT NULL
);

CREATE TABLE answers_cache (
    id SERIAL PRIMARY KEY,
    question TEXT UNIQUE NOT NULL,
    answer TEXT NOT NULL
);
