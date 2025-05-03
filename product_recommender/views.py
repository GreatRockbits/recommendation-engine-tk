# This class contains the Python functions which handle http requests and return responses
# Also contains backend logic

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Product, Summary, Review
from .recommendation_engine.tfidf import tfidf_recommendations
import random

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


def product_detail(request, product_id=None):
    """
    Displays product details and recommendations with paginated reviews.

    Args:
        request: The HTTP request object.
        product_id: The ID of the product to display. If None, a random product is selected.

    Returns:
        An HTTP response with the rendered template.
    """

    if product_id is None: # Random product selection
        try:
            product = Product.objects.order_by('?').first()
            if product is None:
                return HttpResponseNotFound("No products found.")
        except Exception as e:
            print(f"Error selecting random product: {e}")
            return HttpResponseServerError("Internal Server Error")

    else: # Product detail view
        product = get_object_or_404(Product, product_id=product_id)
        
    # Get recommendations
    recommendations = tfidf_recommendations(product)[:3]

    # Get all reviews for the product
    reviews = product.review_set.all()

    # Paginate reviews
    paginator = Paginator(reviews, 5)  # Show 5 reviews per page
    page = request.GET.get('page')
    try:
        reviews_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        reviews_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        reviews_page = paginator.page(paginator.num_pages)

    try:
        # Try to get the summary using the existing model relationship
        summary = Summary.objects.filter(product_id=product).first()
        if summary:
            positive_sentiment = summary.positive_sentiment
            negative_sentiment = summary.negative_sentiment
        else:
            positive_sentiment = "No summary available"
            negative_sentiment = "No summary available"
    except Exception as e:
        print(f"Error accessing summary: {e}")
        positive_sentiment = "No summary available"
        negative_sentiment = "No summary available"

    context = {
        'product': product,
        'recommendations': recommendations,
        'positive_sentiment': positive_sentiment,
        'negative_sentiment': negative_sentiment,
        'reviews_page': reviews_page,
    }

    return render(request, 'product_detail.html', context)
