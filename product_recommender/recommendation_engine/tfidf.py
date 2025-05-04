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

    # Get the target product's summary
    target_summary = target_product.summary.first()
    if not target_summary:
        print(f"Target product {target_product_id} has no summary.")
        return []

    all_products_with_summaries = Product.objects.filter(
        summary__positive_sentiment__isnull=False,
        summary__negative_sentiment__isnull=False
    ).exclude(product_id=target_product_id)

    print(f"Number of all_products_with_summaries: {all_products_with_summaries.count()}")

    positive_summaries = []
    negative_summaries = []
    products_with_summaries = []  # Keep track of products that actually have summaries

    for product in all_products_with_summaries:
        try:
            summary_obj = product.summary.first()  # Get the first (and hopefully only) related Summary object
            if summary_obj:
                positive_summaries.append(summary_obj.positive_sentiment)
                negative_summaries.append(summary_obj.negative_sentiment)
                products_with_summaries.append(product)  # Add to our list of valid products
            else:
                print(f"Warning: Product {product.product_id} (from filtered set) has no summary.")
        except Exception as e:  # Catch any potential errors during access
            print(f"Error accessing summary for product {product.product_id}: {e}")

    if not positive_summaries or not negative_summaries:  # Handle cases where no summaries are found
        print("no summaries found in tfidf")
        return []
    
    positive_tfidf_matrix = positive_vectorizer.fit_transform(positive_summaries)
    target_positive_tfidf = positive_vectorizer.transform([target_summary.positive_sentiment])

    negative_tfidf_matrix = negative_vectorizer.fit_transform(negative_summaries)
    target_negative_tfidf = negative_vectorizer.transform([target_summary.negative_sentiment])

    positive_cosine_similarities = cosine_similarity(target_positive_tfidf, positive_tfidf_matrix).flatten()
    negative_cosine_similarities = cosine_similarity(target_negative_tfidf, negative_tfidf_matrix).flatten()

    combined_similarities = (positive_cosine_similarities + negative_cosine_similarities) / 2

    sorted_indices = combined_similarities.argsort()[::-1]
    top_indices = sorted_indices[:10]

    # Use our filtered list of products that have summaries
    return [products_with_summaries[i] for i in top_indices]