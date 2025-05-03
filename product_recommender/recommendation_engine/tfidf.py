# helper methods for views.py
# circumvents issues around dependency injection, circular imports, encapsulation, and order of operations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ..models import Summary, Product

# Initialize the vectorizers outside the function for better performance
positive_vectorizer = TfidfVectorizer(stop_words='english')
negative_vectorizer = TfidfVectorizer(stop_words='english')

def tfidf_recommendations(target_product):
    target_product_id = target_product.product_id

    all_products_with_summaries = Product.objects.filter(
        summary__positive_sentiment__isnull=False,
        summary__negative_sentiment__isnull=False
    ).exclude(product_id=target_product_id)

    positive_summaries = []
    negative_summaries = []

    for product in all_products_with_summaries:
        if hasattr(product, 'summary'):
            positive_summaries.append(product.summary.positive_sentiment)
            negative_summaries.append(product.summary.negative_sentiment)

    if not positive_summaries or not negative_summaries:  # Handle cases where no summaries are found
        return []

    positive_tfidf_matrix = positive_vectorizer.fit_transform(positive_summaries)
    target_positive_tfidf = positive_vectorizer.transform([target_product.summary.positive_sentiment])

    negative_tfidf_matrix = negative_vectorizer.fit_transform(negative_summaries)
    target_negative_tfidf = negative_vectorizer.transform([target_product.summary.negative_sentiment])

    positive_cosine_similarities = cosine_similarity(target_positive_tfidf, positive_tfidf_matrix).flatten()
    negative_cosine_similarities = cosine_similarity(target_negative_tfidf, negative_tfidf_matrix).flatten()

    combined_similarities = (positive_cosine_similarities + negative_cosine_similarities) / 2

    sorted_indices = combined_similarities.argsort()[::-1]
    top_indices = sorted_indices[:10]

    return [all_products_with_summaries[i] for i in top_indices]