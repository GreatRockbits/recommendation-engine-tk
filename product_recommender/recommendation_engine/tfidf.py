# helper methods for views.py
# circumvents issues around dependency injection, circular imports, encapsulation, and order of operations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ..models import Summary, Product

# Initialize the vectorizers outside the function for better performance
positive_vectorizer = TfidfVectorizer(stop_words='english')
negative_vectorizer = TfidfVectorizer(stop_words='english')

def tfidf_recommendations(target_product):
    """
    Generates recommendations based on TF-IDF similarity, 
    considering both positive and negative sentiments separately.

    Args:
        target_product: The Product object for which to find recommendations.

    Returns:
        A list of Product objects representing the recommended products.
    """

    target_product_id = target_product.product_id 

    # Get all products with summaries
    all_products_with_summaries = Product.objects.filter(
        summary__isnull=False, 
        summary__positive_sentiment__isnull=False, 
        summary__negative_sentiment__isnull=False
    ).exclude(product_id=target_product_id) 

    # Extract summaries
    positive_summaries = [product.summary.positive_sentiment 
                          for product in all_products_with_summaries]
    negative_summaries = [product.summary.negative_sentiment 
                          for product in all_products_with_summaries]

    # Use the initialized vectorizers
    positive_tfidf_matrix = positive_vectorizer.fit_transform(positive_summaries)
    target_positive_tfidf = positive_vectorizer.transform([target_product.summary.positive_sentiment])

    negative_tfidf_matrix = negative_vectorizer.fit_transform(negative_summaries)
    target_negative_tfidf = negative_vectorizer.transform([target_product.summary.negative_sentiment])

    # Calculate cosine similarity for positive and negative sentiments
    positive_cosine_similarities = cosine_similarity(target_positive_tfidf, positive_tfidf_matrix).flatten()
    negative_cosine_similarities = cosine_similarity(target_negative_tfidf, negative_tfidf_matrix).flatten()

    # Combine similarities (e.g., by averaging)
    combined_similarities = (positive_cosine_similarities + negative_cosine_similarities) / 2

    # Get indices of recommended products (sorted by combined similarity)
    sorted_indices = combined_similarities.argsort()[::-1]
    top_indices = sorted_indices[:10]  # Adjust the number of recommendations as needed

    # Return recommended Product objects
    return [all_products_with_summaries[i] for i in top_indices]

# Example usage:
target_product = Product.objects.get(product_id='your_product_id') 
recommendations = tfidf_recommendations(target_product) 
