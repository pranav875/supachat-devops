-- SupaChat Blog Analytics Schema
-- Migration 001: Initial schema

CREATE TABLE IF NOT EXISTS articles (
    id           SERIAL PRIMARY KEY,
    title        TEXT NOT NULL,
    topic        TEXT NOT NULL,
    author       TEXT,
    published_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS article_views (
    id          SERIAL PRIMARY KEY,
    article_id  INT REFERENCES articles(id) ON DELETE CASCADE,
    viewed_date DATE NOT NULL,
    view_count  INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS article_engagement (
    id          SERIAL PRIMARY KEY,
    article_id  INT REFERENCES articles(id) ON DELETE CASCADE,
    event_date  DATE NOT NULL,
    likes       INT NOT NULL DEFAULT 0,
    comments    INT NOT NULL DEFAULT 0,
    shares      INT NOT NULL DEFAULT 0
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_article_views_article_id ON article_views(article_id);
CREATE INDEX IF NOT EXISTS idx_article_views_viewed_date ON article_views(viewed_date);
CREATE INDEX IF NOT EXISTS idx_article_engagement_article_id ON article_engagement(article_id);
CREATE INDEX IF NOT EXISTS idx_article_engagement_event_date ON article_engagement(event_date);
CREATE INDEX IF NOT EXISTS idx_articles_topic ON articles(topic);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
