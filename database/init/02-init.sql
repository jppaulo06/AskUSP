CREATE TABLE jornal_da_usp_articles (
    id SERIAL PRIMARY KEY,
    title TEXT,
    author TEXT,
    date DATE,
    url TEXT,
    content TEXT
);

CREATE TABLE answer_cache (
    id SERIAL PRIMARY KEY,
    question TEXT,
    answer TEXT,
    date DATE
);
