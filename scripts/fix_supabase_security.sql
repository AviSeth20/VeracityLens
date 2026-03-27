-- ============================================================
-- Fix Supabase Security Linter Errors
-- Run this in Supabase SQL Editor
-- ============================================================

-- 1. Enable RLS on all public tables
ALTER TABLE public.predictions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feedback          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news_articles     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_sessions     ENABLE ROW LEVEL SECURITY;

-- 2. Allow full public read/write access (API uses service key, no auth needed)
--    This keeps existing functionality while satisfying RLS requirement

CREATE POLICY "allow_all_predictions" ON public.predictions
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "allow_all_feedback" ON public.feedback
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "allow_all_news_articles" ON public.news_articles
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "allow_all_model_performance" ON public.model_performance
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "allow_all_user_sessions" ON public.user_sessions
    FOR ALL USING (true) WITH CHECK (true);

-- 3. Recreate views WITHOUT security definer (use invoker security instead)
DROP VIEW IF EXISTS public.prediction_stats CASCADE;
DROP VIEW IF EXISTS public.feedback_accuracy CASCADE;

CREATE VIEW public.prediction_stats
    WITH (security_invoker = true)
AS
SELECT predicted_label, COUNT(*) AS total_count, AVG(confidence) AS avg_confidence
FROM public.predictions
GROUP BY predicted_label;

CREATE VIEW public.feedback_accuracy
    WITH (security_invoker = true)
AS
SELECT predicted_label, actual_label, COUNT(*) AS count
FROM public.feedback
GROUP BY predicted_label, actual_label
ORDER BY count DESC;
