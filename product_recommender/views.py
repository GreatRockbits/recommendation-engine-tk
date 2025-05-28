# This class contains the Python functions which handle http requests and return responses
# Also contains backend logic

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError, JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Avg, F
from .models import Product, Summary, Review, RecommendationPerformance
from .recommendation_engine.tfidf import tfidf_recommendations
from .recommendation_engine.tfidf_reviews import tfidf_recommendations_from_reviews
import random
import time
from collections import defaultdict
import html

# --- Helper Function for Unescaping ---
def _unescape_product_name(product_name):
    """
    Unescapes HTML entities in a product name string.
    Returns the unescaped string.
    """
    if product_name:
        return html.unescape(product_name)
    return product_name


def homepage(request):
    """
    Displays the homepage with a product search form and a link to a random product.
    """
    return render(request, 'homepage.html')


def search_results(request):
    """
    Handles product search queries and displays the results.
    """
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(Q(name__icontains=query) | Q(product_id__icontains=query))
        
        # Unescape product names for display
        for product in products:
            product.name = _unescape_product_name(product.name)
            
        context = {'products': products, 'query': query}
        return render(request, 'search_results.html', context)
    else:
        return render(request, 'search_results.html') # Or redirect to homepage with a message
    

def random_product(request):
    """
    Redirects the user to the product detail page of a randomly selected product.
    """
    try:
        random_prod = Product.objects.order_by('?').first()
        if random_prod:
            return redirect('product_detail', product_id=random_prod.product_id)
        else:
            return render(request, 'homepage.html', {'message': 'No products available.'})
    except Exception as e:
        print(f"Error selecting random product: {e}")
        return render(request, 'homepage.html', {'error': 'Error fetching a random product.'})


def _get_product(product_id=None):
    """Fetches a product instance, either by ID or a random one."""
    if product_id:
        product = get_object_or_404(Product, product_id=product_id)
    else:
        try:
            product = Product.objects.order_by('?').first()
            if product is None:
                raise Product.DoesNotExist("No products found.")
        except Product.DoesNotExist as e:
            raise HttpResponseNotFound(str(e))
        except Exception as e:
            print(f"Error selecting random product: {e}")
            raise HttpResponseServerError("Internal Server Error")
    
    # Unescape the product name if found
    product.name = _unescape_product_name(product.name)
    return product

def _get_recommendations_from_summary(product):
    """Gets recommendations using the AI summary TF-IDF."""
    start_time = time.time()
    recommendations = tfidf_recommendations(product)[:4]
    end_time = time.time()
    time_taken = end_time - start_time
    
    # Unescape product names in recommendations
    for rec in recommendations:
        rec.name = _unescape_product_name(rec.name)
        
    return recommendations, "{:.4f} seconds".format(time_taken)

def _get_recommendations_from_reviews(product):
    """Gets recommendations using the raw review text TF-IDF."""
    start_time = time.time()
    recommendations = tfidf_recommendations_from_reviews(product)[:4]
    end_time = time.time()
    time_taken = end_time - start_time
    
    # Unescape product names in recommendations
    for rec in recommendations:
        rec.name = _unescape_product_name(rec.name)
        
    return recommendations, "{:.4f} seconds".format(time_taken)

def _get_product_summary(product):
    """Fetches the positive and negative sentiment summary for a product."""
    try:
        summary = Summary.objects.filter(product_id=product).first()
        if summary:
            return summary.positive_sentiment, summary.negative_sentiment
        else:
            return "No summary available", "No summary available"
    except Exception as e:
        print(f"Error accessing summary: {e}")
        return "No summary available", "No summary available"

def _paginate_reviews(request, reviews, reviews_per_page=5):
    """Paginates the reviews for a product."""
    paginator = Paginator(reviews, reviews_per_page)
    page = request.GET.get('page')
    try:
        reviews_page = paginator.page(page)
    except PageNotAnInteger:
        reviews_page = paginator.page(1)
    except EmptyPage:
        reviews_page = paginator.page(paginator.num_pages)
    return reviews_page

def product_detail(request, product_id=None):
    """
    Displays basic product details. Recommendations and reviews are loaded via AJAX.
    """
    try:
        product = _get_product(product_id)
        positive_sentiment, negative_sentiment = _get_product_summary(product)

        context = {
            'product': product,
            'positive_sentiment': positive_sentiment,
            'negative_sentiment': negative_sentiment,
        }

        return render(request, 'product_detail.html', context)

    except (HttpResponseNotFound, HttpResponseServerError) as e:
        return e
    except Exception as e:
        print(f"An unexpected error occurred in product_detail: {e}")
        return HttpResponseServerError("Internal Server Error")


def api_recommendations_both(request, product_id):
    """API endpoint for loading both types of recommendations."""
    try:
        product = get_object_or_404(Product, product_id=product_id)
        
        # Get both recommendation types
        summary_recs, summary_time_str = _get_recommendations_from_summary(product)
        reviews_recs, reviews_time_str = _get_recommendations_from_reviews(product)
        
        # Parse times
        summary_time = float(summary_time_str.split(' ')[0])
        reviews_time = float(reviews_time_str.split(' ')[0])
        
        # Save performance data
        num_reviews = product.review_set.count()
        RecommendationPerformance.objects.create(
            product_id=product,
            summary_time=summary_time,
            reviews_time=reviews_time,
            num_reviews=num_reviews
        )
        
        # Convert to JSON format...
        return JsonResponse({
            'summary_recommendations': summary_data,
            'reviews_recommendations': reviews_data,
            'summary_time': summary_time_str,
            'reviews_time': reviews_time_str,
        })
    except Exception as e:
        print(f"Error in api_recommendations_reviews: {e}")
        return JsonResponse({'error': 'Failed to load recommendations'}, status=500)


def api_reviews(request, product_id):
    """API endpoint for loading paginated reviews."""
    try:
        product = get_object_or_404(Product, product_id=product_id)
        reviews = product.review_set.all()
        
        # Pagination
        paginator = Paginator(reviews, 5)  # 5 reviews per page
        page = request.GET.get('page', 1)
        
        try:
            reviews_page = paginator.page(page)
        except PageNotAnInteger:
            reviews_page = paginator.page(1)
        except EmptyPage:
            reviews_page = paginator.page(paginator.num_pages)
        
        # Convert reviews to JSON-serializable format
        reviews_data = []
        for review in reviews_page:
            reviews_data.append({
                'review_text': review.review_text or "No review text",
            })
        
        return JsonResponse({
            'reviews': reviews_data,
            'has_previous': reviews_page.has_previous(),
            'has_next': reviews_page.has_next(),
            'previous_page_number': reviews_page.previous_page_number() if reviews_page.has_previous() else None,
            'next_page_number': reviews_page.next_page_number() if reviews_page.has_next() else None,
            'current_page': reviews_page.number,
            'total_pages': paginator.num_pages,
        })
    except Exception as e:
        print(f"Error in api_reviews: {e}")
        return JsonResponse({'error': 'Failed to load reviews'}, status=500)


def api_recommendations_both(request, product_id):
    """API endpoint for loading both types of recommendations and saving performance data."""
    try:
        product = get_object_or_404(Product, product_id=product_id)
        
        # Get both recommendation types
        summary_recs, summary_time_str = _get_recommendations_from_summary(product)
        reviews_recs, reviews_time_str = _get_recommendations_from_reviews(product)
        
        # Parse times
        summary_time = float(summary_time_str.split(' ')[0])
        reviews_time = float(reviews_time_str.split(' ')[0])
        
        # Save performance data
        num_reviews = product.review_set.count()
        RecommendationPerformance.objects.create(
            product_id=product,
            summary_time=summary_time,
            reviews_time=reviews_time,
            num_reviews=num_reviews
        )
        
        # Convert recommendations to JSON-serializable format
        summary_data = []
        for rec in summary_recs:
            summary_data.append({
                'product_id': rec.product_id,
                'name': rec.name,
                'price': str(rec.price),
                'image_url': rec.image_url,
            })
        
        reviews_data = []
        for rec in reviews_recs:
            reviews_data.append({
                'product_id': rec.product_id,
                'name': rec.name,
                'price': str(rec.price),
                'image_url': rec.image_url,
            })
        
        return JsonResponse({
            'summary_recommendations': summary_data,
            'reviews_recommendations': reviews_data,
            'summary_time': summary_time_str,
            'reviews_time': reviews_time_str,
            'time_saved': "{:.4f} seconds".format(reviews_time - summary_time),
            'num_reviews': num_reviews,
        })
        
    except Exception as e:
        print(f"Error in api_recommendations_both: {e}")
        return JsonResponse({'error': 'Failed to load recommendations'}, status=500)


def recommendation_analytics(request):
    """
    Displays analytics on recommendation performance with bar graphs.
    Now optimized to work with the unified API approach.
    """
    try:
        # Get performance data with related product information
        performance_data = RecommendationPerformance.objects.all().select_related('product_id')
        
        if not performance_data.exists():
            # Handle case where no performance data exists yet
            context = {
                'analytics_data': [],
                'average_time_saved': 0,
                'average_summary_time': 0,
                'average_reviews_time': 0,
                'product_names': [],
                'review_numbers': [],
                'average_time_saved_by_review': [],
                'no_data': True,
            }
            return render(request, 'recommendation_analytics.html', context)
        
        # Calculate overall averages using database aggregation
        averages = RecommendationPerformance.objects.aggregate(
            avg_summary_time=Avg('summary_time'),
            avg_reviews_time=Avg('reviews_time'),
            avg_time_saved=Avg(F('reviews_time') - F('summary_time'))
        )
        
        average_summary_time = averages['avg_summary_time'] or 0
        average_reviews_time = averages['avg_reviews_time'] or 0
        average_time_saved = averages['avg_time_saved'] or 0
        
        # Prepare data for charts and tables
        analytics = []
        product_names = []
        time_saved_by_review_count = defaultdict(list)
        
        for data in performance_data:
            time_saved = data.reviews_time - data.summary_time
            
            # Unescape product name for display
            product_name = _unescape_product_name(data.product_id.name)
            
            analytics.append({
                'product_name': product_name,
                'product_id': data.product_id.product_id,
                'summary_time': round(data.summary_time, 4),
                'reviews_time': round(data.reviews_time, 4),
                'num_reviews': data.num_reviews,
                'time_saved': round(time_saved, 4),
                'efficiency_ratio': round((time_saved / data.reviews_time) * 100, 1) if data.reviews_time > 0 else 0,
            })
            
            product_names.append(product_name)
            time_saved_by_review_count[data.num_reviews].append(time_saved)
        
        # Calculate average time saved by review count for the second chart
        average_time_saved_by_review_count = {}
        for review_count, time_saved_list in time_saved_by_review_count.items():
            avg_time_saved = sum(time_saved_list) / len(time_saved_list)
            average_time_saved_by_review_count[review_count] = round(avg_time_saved, 4)
        
        # Prepare data for charts
        review_numbers = sorted(average_time_saved_by_review_count.keys())
        average_time_saved_values = [
            average_time_saved_by_review_count[count] for count in review_numbers
        ]
        
        # Sort analytics by time saved (descending) for better display
        analytics.sort(key=lambda x: x['time_saved'], reverse=True)
        
        # Additional statistics
        total_products_analyzed = performance_data.count()
        max_time_saved = max((item['time_saved'] for item in analytics), default=0)
        min_time_saved = min((item['time_saved'] for item in analytics), default=0)
        
        context = {
            'analytics_data': analytics,
            'average_time_saved': round(average_time_saved, 4),
            'average_summary_time': round(average_summary_time, 4),
            'average_reviews_time': round(average_reviews_time, 4),
            'product_names': product_names,
            'review_numbers': review_numbers,
            'average_time_saved_by_review': average_time_saved_values,
            'total_products_analyzed': total_products_analyzed,
            'max_time_saved': round(max_time_saved, 4),
            'min_time_saved': round(min_time_saved, 4),
            'no_data': False,
        }
        
        return render(request, 'recommendation_analytics.html', context)
        
    except Exception as e:
        print(f"Error in recommendation_analytics: {e}")
        # Return empty context with error flag
        context = {
            'analytics_data': [],
            'average_time_saved': 0,
            'average_summary_time': 0,
            'average_reviews_time': 0,
            'product_names': [],
            'review_numbers': [],
            'average_time_saved_by_review': [],
            'error': 'Failed to load analytics data',
        }
        return render(request, 'recommendation_analytics.html', context)


# Optional: Clean up function to remove duplicate performance records
def cleanup_duplicate_performance_records():
    """
    Utility function to clean up any duplicate RecommendationPerformance records
    that might have been created by the old API structure.
    Call this once after implementing the new unified API.
    """
    from django.db.models import Count
    
    # Find products with multiple performance records
    duplicates = (RecommendationPerformance.objects
                 .values('product_id')
                 .annotate(count=Count('id'))
                 .filter(count__gt=1))
    
    for duplicate in duplicates:
        product_id = duplicate['product_id']
        # Keep the most recent record, delete the rest
        records = RecommendationPerformance.objects.filter(
            product_id=product_id
        ).order_by('-id')
        
        # Delete all but the first (most recent) record
        records[1:].delete()
    
    print(f"Cleaned up {len(duplicates)} duplicate performance record groups")