"""
Category classifier using Naive Bayes + TF-IDF.
Model is trained once on startup and reused — not retrained per request.
"""
import re
import os
import joblib  # type: ignore[import]
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore[import]
from sklearn.naive_bayes import MultinomialNB  # type: ignore[import]
from sklearn.pipeline import Pipeline  # type: ignore[import]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "category_model.pkl")

TRAINING_DATA = [
    # Food & Dining
    ("swiggy order", "food"),
    ("zomato food delivery", "food"),
    ("pizza hut", "food"),
    ("dominos pizza", "food"),
    ("burger king", "food"),
    ("mcdonalds", "food"),
    ("restaurant dinner", "food"),
    ("cafe coffee day", "food"),
    ("starbucks coffee", "food"),
    ("grocery store", "food"),
    ("supermarket vegetables", "food"),
    ("big basket order", "food"),
    ("blinkit groceries", "food"),
    # Travel & Transport
    ("uber ride", "travel"),
    ("ola cab", "travel"),
    ("rapido bike", "travel"),
    ("bus ticket booking", "travel"),
    ("train ticket irctc", "travel"),
    ("flight booking indigo", "travel"),
    ("metro card recharge", "travel"),
    ("petrol fuel", "travel"),
    ("parking fee", "travel"),
    ("auto rickshaw", "travel"),
    # Shopping
    ("amazon order", "shopping"),
    ("flipkart purchase", "shopping"),
    ("myntra clothes", "shopping"),
    ("meesho fashion", "shopping"),
    ("ajio apparel", "shopping"),
    ("nykaa beauty products", "shopping"),
    ("reliance mall", "shopping"),
    ("electronics purchase", "shopping"),
    ("mobile accessories", "shopping"),
    # Entertainment
    ("netflix subscription", "entertainment"),
    ("amazon prime video", "entertainment"),
    ("hotstar subscription", "entertainment"),
    ("spotify music", "entertainment"),
    ("movie ticket bookmyshow", "entertainment"),
    ("concert event ticket", "entertainment"),
    ("gaming purchase", "entertainment"),
    ("youtube premium", "entertainment"),
    # Health & Wellness
    ("gym membership", "health"),
    ("doctor consultation", "health"),
    ("pharmacy medicine", "health"),
    ("hospital bill", "health"),
    ("dental clinic", "health"),
    ("pathology lab test", "health"),
    ("yoga class", "health"),
    ("spa treatment", "health"),
    ("massage therapy", "health"),
    ("salon haircut", "health"),
    # Utilities & Bills
    ("electricity bill", "utilities"),
    ("water bill payment", "utilities"),
    ("internet recharge broadband", "utilities"),
    ("mobile phone recharge", "utilities"),
    ("gas cylinder booking", "utilities"),
    ("dth cable tv recharge", "utilities"),
    ("insurance premium", "utilities"),
    # Education
    ("udemy course", "education"),
    ("coursera subscription", "education"),
    ("college tuition fee", "education"),
    ("books stationery", "education"),
    ("online class", "education"),
    # Finance & Banking
    ("emi payment loan", "finance"),
    ("credit card bill", "finance"),
    ("mutual fund sip", "finance"),
    ("fd investment", "finance"),
    ("bank charges", "finance"),
]

texts = [t for t, _ in TRAINING_DATA]
labels = [l for _, l in TRAINING_DATA]


def _build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, stop_words="english")),
        ("clf", MultinomialNB(alpha=0.5)),
    ])


def _load_or_train() -> Pipeline:
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    pipeline = _build_pipeline()
    pipeline.fit(texts, labels)
    joblib.dump(pipeline, MODEL_PATH)
    return pipeline


# Load once at module import — not per request
_pipeline = None

def get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = _load_or_train()
    return _pipeline

CATEGORIES = sorted(set(labels))


def predict_category(description: str) -> tuple[str, float]:
    """Returns (category, confidence_percent)."""
    clean = re.sub(r"[^a-zA-Z\s]", " ", description.lower()).strip()
    if not clean:
        return "uncategorized", 0.0
    proba = get_pipeline().predict_proba([clean])[0]
    idx = proba.argmax()
    category = get_pipeline().classes_[idx]
    confidence = round(float(proba[idx]) * 100, 2)  # type: ignore[import]
    return category, confidence


def retrain(new_texts: list[str], new_labels: list[str]) -> None:
    """Retrain with additional data and persist."""
    global _pipeline
    all_texts = texts + new_texts
    all_labels = labels + new_labels
    _pipeline = _build_pipeline()
    _pipeline.fit(all_texts, all_labels)
    joblib.dump(_pipeline, MODEL_PATH)
