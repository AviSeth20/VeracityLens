-- Supabase Database Schema for Fake News Detection
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id VARCHAR(255) NOT NULL,
    text TEXT,
    predicted_label VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    explanation JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for faster queries
    CONSTRAINT predictions_article_id_idx UNIQUE (article_id)
);

CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_label ON predictions(predicted_label);
CREATE INDEX IF NOT EXISTS idx_predictions_model ON predictions(model_name);

-- Feedback table for active learning
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id VARCHAR(255) NOT NULL,
    predicted_label VARCHAR(50) NOT NULL,
    actual_label VARCHAR(50) NOT NULL,
    user_comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key to predictions
    CONSTRAINT fk_article FOREIGN KEY (article_id) 
        REFERENCES predictions(article_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_article ON feedback(article_id);

-- News articles cache table
CREATE TABLE IF NOT EXISTS news_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    content TEXT,
    url TEXT UNIQUE NOT NULL,
    image_url TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    source_name VARCHAR(255),
    source_url TEXT,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analyzed BOOLEAN DEFAULT FALSE,
    
    -- Analysis results
    prediction_id UUID,
    CONSTRAINT fk_prediction FOREIGN KEY (prediction_id) 
        REFERENCES predictions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_news_published ON news_articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_analyzed ON news_articles(analyzed);
CREATE INDEX IF NOT EXISTS idx_news_source ON news_articles(source_name);

-- Model performance tracking
CREATE TABLE IF NOT EXISTS model_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    accuracy FLOAT,
    precision FLOAT,
    recall FLOAT,
    f1_score FLOAT,
    total_predictions INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_performance_model ON model_performance(model_name);
CREATE INDEX IF NOT EXISTS idx_performance_date ON model_performance(evaluated_at DESC);

-- User sessions (optional - for tracking user interactions)
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_agent TEXT,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_id ON user_sessions(session_id);

-- Views for analytics

-- Prediction statistics by label
CREATE OR REPLACE VIEW prediction_stats AS
SELECT 
    predicted_label,
    COUNT(*) as total_count,
    AVG(confidence) as avg_confidence,
    MIN(confidence) as min_confidence,
    MAX(confidence) as max_confidence,
    COUNT(DISTINCT model_name) as models_used
FROM predictions
GROUP BY predicted_label;

-- Daily prediction volume
CREATE OR REPLACE VIEW daily_predictions AS
SELECT 
    DATE(created_at) as prediction_date,
    COUNT(*) as total_predictions,
    COUNT(DISTINCT article_id) as unique_articles,
    AVG(confidence) as avg_confidence
FROM predictions
GROUP BY DATE(created_at)
ORDER BY prediction_date DESC;

-- Feedback accuracy (where we have feedback)
CREATE OR REPLACE VIEW feedback_accuracy AS
SELECT 
    f.predicted_label,
    f.actual_label,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM feedback f
GROUP BY f.predicted_label, f.actual_label
ORDER BY count DESC;

-- Model comparison
CREATE OR REPLACE VIEW model_comparison AS
SELECT 
    p.model_name,
    COUNT(*) as total_predictions,
    AVG(p.confidence) as avg_confidence,
    COUNT(f.id) as feedback_count,
    SUM(CASE WHEN f.predicted_label = f.actual_label THEN 1 ELSE 0 END) as correct_predictions,
    ROUND(100.0 * SUM(CASE WHEN f.predicted_label = f.actual_label THEN 1 ELSE 0 END) / 
          NULLIF(COUNT(f.id), 0), 2) as accuracy_percentage
FROM predictions p
LEFT JOIN feedback f ON p.article_id = f.article_id
GROUP BY p.model_name;

-- Row Level Security (RLS) Policies
-- Enable RLS on tables
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_performance ENABLE ROW LEVEL SECURITY;

-- Allow public read access (adjust based on your security needs)
CREATE POLICY "Allow public read access on predictions" 
    ON predictions FOR SELECT 
    USING (true);

CREATE POLICY "Allow public insert on predictions" 
    ON predictions FOR INSERT 
    WITH CHECK (true);

CREATE POLICY "Allow public read access on feedback" 
    ON feedback FOR SELECT 
    USING (true);

CREATE POLICY "Allow public insert on feedback" 
    ON feedback FOR INSERT 
    WITH CHECK (true);

CREATE POLICY "Allow public read access on news_articles" 
    ON news_articles FOR SELECT 
    USING (true);

CREATE POLICY "Allow public insert on news_articles" 
    ON news_articles FOR INSERT 
    WITH CHECK (true);

-- Functions

-- Function to update model performance based on feedback
CREATE OR REPLACE FUNCTION update_model_performance()
RETURNS TRIGGER AS $$
BEGIN
    -- Update performance metrics when new feedback is added
    INSERT INTO model_performance (
        model_name,
        total_predictions,
        correct_predictions,
        accuracy
    )
    SELECT 
        p.model_name,
        COUNT(*) as total,
        SUM(CASE WHEN f.predicted_label = f.actual_label THEN 1 ELSE 0 END) as correct,
        ROUND(100.0 * SUM(CASE WHEN f.predicted_label = f.actual_label THEN 1 ELSE 0 END) / COUNT(*), 2) as accuracy
    FROM predictions p
    INNER JOIN feedback f ON p.article_id = f.article_id
    WHERE p.model_name = (
        SELECT model_name FROM predictions WHERE article_id = NEW.article_id
    )
    GROUP BY p.model_name
    ON CONFLICT (model_name) DO UPDATE SET
        total_predictions = EXCLUDED.total_predictions,
        correct_predictions = EXCLUDED.correct_predictions,
        accuracy = EXCLUDED.accuracy,
        evaluated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update performance on new feedback
CREATE TRIGGER trigger_update_performance
    AFTER INSERT ON feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_model_performance();

-- Comments for documentation
COMMENT ON TABLE predictions IS 'Stores all model predictions with confidence scores and explanations';
COMMENT ON TABLE feedback IS 'User feedback for active learning and model improvement';
COMMENT ON TABLE news_articles IS 'Cache of fetched news articles from GNews API';
COMMENT ON TABLE model_performance IS 'Tracks model performance metrics over time';

-- Grant permissions (adjust based on your needs)
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO postgres;
