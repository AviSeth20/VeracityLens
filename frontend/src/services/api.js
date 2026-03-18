import axios from "axios";

const BASE_URL =
  import.meta.env.VITE_API_URL ?? "https://aviseth-fake-news-api.hf.space";

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

/** Analyze a news article — returns real model prediction */
export async function analyzeNews(text, model = "distilbert") {
  const { data } = await client.post("/predict", { text, model });
  return data;
}

/** Fetch live news articles from GNews */
export async function fetchNews(query = "breaking news", max = 8) {
  const { data } = await client.get("/news", {
    params: { query, max_results: max },
  });
  return data;
}

/** Submit user feedback on a prediction */
export async function submitFeedback(
  articleId,
  predictedLabel,
  actualLabel,
  comment = "",
) {
  const { data } = await client.post("/feedback", {
    article_id: articleId,
    predicted_label: predictedLabel,
    actual_label: actualLabel,
    user_comment: comment,
  });
  return data;
}

/** Get prediction statistics */
export async function getStats() {
  const { data } = await client.get("/stats");
  return data?.statistics ?? null;
}

/** Fetch newspaper — all news grouped by predicted label */
export async function getNewspaper(maxPerTopic = 6) {
  const { data } = await client.get("/news/newspaper", {
    params: { max_per_topic: maxPerTopic },
  });
  return data;
}

/** Get attention + optional SHAP explanation for a text */
export async function explainPrediction(
  text,
  model = "distilbert",
  deep = false,
) {
  const { data } = await client.post("/explain", { text, model, deep });
  return data;
}
