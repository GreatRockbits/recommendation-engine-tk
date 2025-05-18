# helper methods for views.py
# circumvents issues around dependency injection, circular imports, encapsulation, and order of operations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ..models import Review, Product
import time

# Initialize the vectorizer for review text outside the function
review_vectorizer = TfidfVectorizer(stop_words='english')
PRODUCT_LIMIT = 5000

def tfidf_recommendations_from_reviews(target_product):
    target_product_id = target_product.product_id

    # Get all reviews for all products
    all_reviews = Review.objects.all().select_related('product_id')
    limited_products = Product.objects.all()[:PRODUCT_LIMIT]
    all_reviews_limited = Review.objects.filter(product_id__in=limited_products).select_related('product_id')

    # Filter reviews for the target product
    target_reviews = all_reviews.filter(product_id=target_product)
    target_review_texts = [review.review_text for review in target_reviews if review.review_text]

    # Get review texts for all other products and their IDs
    other_reviews_with_ids = [(review.review_text, review.product_id) for review in all_reviews_limited.exclude(product_id=target_product) if review.review_text]
    other_review_texts, other_product_ids = zip(*other_reviews_with_ids) if other_reviews_with_ids else ([], [])

    if not target_review_texts or not other_review_texts:
        print("Not enough review text available to calculate TF-IDF.")
        return []

    # Fit and transform the review texts
    review_vectorizer.fit(review.review_text for review in all_reviews_limited if review.review_text)
    target_tfidf = review_vectorizer.transform(target_review_texts)
    other_tfidf = review_vectorizer.transform(other_review_texts)

    if not other_tfidf.shape[0]:
        print("No other product reviews to compare against.")
        return []

    # Calculate cosine similarities
    cosine_similarities = cosine_similarity(target_tfidf, other_tfidf).mean(axis=0)

    # Sort by similarity
    sorted_indices = cosine_similarities.argsort()[::-1]
    top_indices = sorted_indices[:10]

    # Return the top similar product IDs and the time taken
    recommendations = [other_product_ids[i] for i in top_indices]
    return recommendations