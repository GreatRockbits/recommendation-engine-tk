# helper methods for views.py
# circumvents issues around dependency injection, circular imports, encapsulation, and order of operations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ..models import Summary, Product, Review
import time

# Initialize fresh vectorizers for each call to avoid fitting conflicts
def get_fresh_positive_vectorizer():
    return TfidfVectorizer(stop_words='english')

def get_fresh_negative_vectorizer():
    return TfidfVectorizer(stop_words='english')

PRODUCT_LIMIT = 5000

def tfidf_recommendations(target_product):
    target_product_id = target_product.product_id

    # Get the target product's summary
    target_summary = target_product.summary.first()
    if not target_summary:
        print(f"Target product {target_product_id} has no summary.")
        return []

    # Use prefetch_related for reverse foreign key relationships
    # This eliminates the N+1 query problem by fetching summaries in a separate optimized query
    products_with_summaries = Product.objects.prefetch_related('summary').filter(
        summary__positive_sentiment__isnull=False,
        summary__negative_sentiment__isnull=False
    ).exclude(product_id=target_product_id)[:PRODUCT_LIMIT]

    print(f"Number of products_with_summaries: {len(products_with_summaries)}")

    # Build lists directly from the prefetched query results
    valid_products = []
    positive_summaries = []
    negative_summaries = []

    for product in products_with_summaries:
        # Access prefetched summaries directly without additional database hits
        summaries = list(product.summary.all())  # Convert to list to access prefetched data
        if summaries:
            summary_obj = summaries[0]  # Get the first summary
            if summary_obj.positive_sentiment and summary_obj.negative_sentiment:
                valid_products.append(product)
                positive_summaries.append(summary_obj.positive_sentiment)
                negative_summaries.append(summary_obj.negative_sentiment)

    if not positive_summaries:  # This also covers negative_summaries since they're populated together
        print("no summaries found in tfidf")
        return []

    # Get fresh vectorizer instances to avoid fitting conflicts
    positive_vectorizer = get_fresh_positive_vectorizer()
    negative_vectorizer = get_fresh_negative_vectorizer()

    # Combine target summaries with all summaries to fit vectorizer once
    all_positive = [target_summary.positive_sentiment] + positive_summaries
    all_negative = [target_summary.negative_sentiment] + negative_summaries

    # Fit and transform in one step
    positive_tfidf_matrix = positive_vectorizer.fit_transform(all_positive)
    negative_tfidf_matrix = negative_vectorizer.fit_transform(all_negative)

    # Extract target vectors (first row) and comparison vectors
    target_positive_tfidf = positive_tfidf_matrix[0:1]
    comparison_positive_tfidf = positive_tfidf_matrix[1:]
    
    target_negative_tfidf = negative_tfidf_matrix[0:1]
    comparison_negative_tfidf = negative_tfidf_matrix[1:]

    # Calculate similarities
    positive_cosine_similarities = cosine_similarity(target_positive_tfidf, comparison_positive_tfidf).flatten()
    negative_cosine_similarities = cosine_similarity(target_negative_tfidf, comparison_negative_tfidf).flatten()

    # Combine similarities and get top 10
    combined_similarities = (positive_cosine_similarities + negative_cosine_similarities) * 0.5

    # Use argpartition for better performance when we only need top K
    if len(combined_similarities) <= 10:
        top_indices = combined_similarities.argsort()[::-1]
    else:
        # argpartition is O(n) vs O(n log n) for full sort
        top_k_indices = (-combined_similarities).argpartition(10)[:10]
        top_indices = top_k_indices[(-combined_similarities[top_k_indices]).argsort()]

    return [valid_products[i] for i in top_indices]