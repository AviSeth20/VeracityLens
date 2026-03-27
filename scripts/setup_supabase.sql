DROP TABLE IF EXISTS feedback          CASCADE;
DROP TABLE IF EXISTS predictions       CASCADE;
DROP TABLE IF EXISTS news_articles     CASCADE;
DROP TABLE IF EXISTS model_performance CASCADE;
DROP TABLE IF EXISTS user_sessions     CASCADE;

DROP VIEW IF EXISTS prediction_stats   CASCADE;
DROP VIEW IF EXISTS daily_predictions  CASCADE;
DROP VIEW IF EXISTS feedback_accuracy  CASCADE;
DROP VIEW IF EXISTS model_comparison   CASCADE;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE predictions (
    id              UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id      VARCHAR      NOT NULL UNIQUE,
    text            TEXT,
    predicted_label VARCHAR(50)  NOT NULL,
    confidence      FLOAT        NOT NULL,
    model_name      VARCHAR(100) NOT NULL,
    explanation     JSONB,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX idx_pred_created ON predictions(created_at DESC);
CREATE INDEX idx_pred_label   ON predictions(predicted_label);
CREATE INDEX idx_pred_model   ON predictions(model_name);

CREATE TABLE feedback (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id      VARCHAR     NOT NULL,
    predicted_label VARCHAR(50) NOT NULL,
    actual_label    VARCHAR(50) NOT NULL,
    user_comment    TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_fb_created ON feedback(created_at DESC);
CREATE INDEX idx_fb_article ON feedback(article_id);

CREATE TABLE news_articles (
    id            UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    title         TEXT         NOT NULL,
    description   TEXT,
    content       TEXT,
    url           TEXT         NOT NULL UNIQUE,
    image_url     TEXT,
    published_at  TIMESTAMPTZ,
    source_name   VARCHAR(255),
    source_url    TEXT,
    fetched_at    TIMESTAMPTZ  DEFAULT NOW(),
    analyzed      BOOLEAN      DEFAULT FALSE,
    prediction_id UUID
);

CREATE INDEX idx_news_published ON news_articles(published_at DESC);
CREATE INDEX idx_news_analyzed  ON news_articles(analyzed);

CREATE TABLE model_performance (
    id                  UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name          VARCHAR(100) NOT NULL,
    accuracy            FLOAT,
    precision           FLOAT,
    recall              FLOAT,
    f1_score            FLOAT,
    total_predictions   INTEGER      DEFAULT 0,
    correct_predictions INTEGER      DEFAULT 0,
    evaluated_at        TIMESTAMPTZ  DEFAULT NOW()
);

CREATE TABLE user_sessions (
    id            UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id    VARCHAR     NOT NULL UNIQUE,
    user_agent    TEXT,
    ip_address    INET,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE predictions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback          ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_articles     ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions     ENABLE ROW LEVEL SECURITY;

CREATE POLICY "allow_all_predictions"      ON predictions      FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_feedback"         ON feedback         FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_news_articles"    ON news_articles    FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_model_performance" ON model_performance FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_user_sessions"    ON user_sessions    FOR ALL USING (true) WITH CHECK (true);

CREATE VIEW prediction_stats WITH (security_invoker = true) AS
SELECT predicted_label, COUNT(*) AS total_count, AVG(confidence) AS avg_confidence
FROM predictions
GROUP BY predicted_label;

CREATE VIEW feedback_accuracy WITH (security_invoker = true) AS
SELECT predicted_label, actual_label, COUNT(*) AS count
FROM feedback
GROUP BY predicted_label, actual_label
ORDER BY count DESC;
