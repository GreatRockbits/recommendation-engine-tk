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


# API Endpoints for AJAX loading
def api_recommendations_summary(request, product_id):
    """API endpoint for loading recommendations based on AI summary."""
    try:
        product = get_object_or_404(Product, product_id=product_id)
        recommendations, time_taken = _get_recommendations_from_summary(product)
        
        # Convert recommendations to JSON-serializable format
        recommendations_data = []
        for rec in recommendations:
            recommendations_data.append({
                'product_id': rec.product_id,
                'name': rec.name,
                'price': str(rec.price),
                'image_url': rec.image_url,
            })
        
        return JsonResponse({
            'recommendations': recommendations_data,
            'time_taken': time_taken,
        })
    except Exception as e:
        print(f"Error in api_recommendations_summary: {e}")
        return JsonResponse({'error': 'Failed to load recommendations'}, status=500)


def api_recommendations_reviews(request, product_id):
    """API endpoint for loading recommendations based on review text."""
    try:
        product = get_object_or_404(Product, product_id=product_id)
        recommendations, time_taken = _get_recommendations_from_reviews(product)
        
        # Convert recommendations to JSON-serializable format
        recommendations_data = []
        for rec in recommendations:
            recommendations_data.append({
                'product_id': rec.product_id,
                'name': rec.name,
                'price': str(rec.price),
                'image_url': rec.image_url,
            })
        
        # Save performance data after both recommendation types are generated
        # We'll need to coordinate this with the summary API call
        reviews = product.review_set.all()
        num_reviews = reviews.count()
        
        # Get the summary time if it exists (this is a simplified approach)
        # In a real scenario, you might want to store this in session or cache
        summary_time_obj = RecommendationPerformance.objects.filter(
            product_id=product
        ).order_by('-id').first()
        
        if summary_time_obj:
            # Update the existing record
            summary_time_obj.reviews_time = float(time_taken.split(' ')[0])
            summary_time_obj.save()
        else:
            # Create a new record (this shouldn't happen in normal flow)
            RecommendationPerformance.objects.create(
                product_id=product,
                summary_time=0,  # Will be updated by summary API
                reviews_time=float(time_taken.split(' ')[0]),
                num_reviews=num_reviews
            )
        
        return JsonResponse({
            'recommendations': recommendations_data,
            'time_taken': time_taken,
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


def recommendation_analytics(request):
    """Displays analytics on recommendation performance with bar graphs."""
    # Calculate the average summary time and average reviews time
    average_summary_time = RecommendationPerformance.objects.aggregate(Avg('summary_time'))['summary_time__avg'] or 0
    average_reviews_time = RecommendationPerformance.objects.aggregate(Avg('reviews_time'))['reviews_time__avg'] or 0

    performance_data = RecommendationPerformance.objects.all().select_related('product_id')

    analytics = []
    time_saved_data = []
    review_counts = []
    product_names = []

    # Aggregate time saved by the number of reviews
    time_saved_by_review_count = defaultdict(list)
    for data in performance_data:
        time_saved = data.reviews_time - data.summary_time
        time_saved_by_review_count[data.num_reviews].append(time_saved)

        # Unescape product name for display
        product_name = _unescape_product_name(data.product_id.name)
        
        analytics.append({
            'product_name': product_name,
            'summary_time': data.summary_time,
            'reviews_time': data.reviews_time,
            'num_reviews': data.num_reviews,
            'time_saved': time_saved,
        })
        time_saved_data.append(time_saved)
        review_counts.append(data.num_reviews)
        product_names.append(product_name)

    # Calculate the average time saved for each review count
    average_time_saved_by_review_count = {
        count: sum(times) / len(times)
        for count, times in time_saved_by_review_count.items()
    }

    # Prepare data for the second chart
    review_numbers = sorted(average_time_saved_by_review_count.keys())
    average_time_saved_values = [average_time_saved_by_review_count[count] for count in review_numbers]

    average_time_saved = RecommendationPerformance.objects.annotate(
        time_saved=F('reviews_time') - F('summary_time')
    ).aggregate(Avg('time_saved'))['time_saved__avg']

    context = {
        'analytics_data': analytics,
        'average_time_saved': average_time_saved,
        'average_summary_time': average_summary_time,
        'average_reviews_time': average_reviews_time,
        'product_names': product_names,
        'review_numbers': review_numbers,  # For the x-axis of the second chart
        'average_time_saved_by_review': average_time_saved_values, # For the y-axis of the second chart
    }
    return render(request, 'recommendation_analytics.html', context)