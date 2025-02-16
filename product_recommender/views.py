# This class contains the Python functions which handle http requests and return responses
# Also contains backend logic

from django.shortcuts import render, get_object_or_404
from .models import Product, Summary
from .recommendation_engine.tfidf import tfidf_recommendations
import random

def product_detail(request, product_id=None):
    """
    Displays product details and recommendations.

    Args:
        request: The HTTP request object.
        product_id: The ID of the product to display. If None, a random product is selected.

    Returns:
        An HTTP response with the rendered template.
    """

    if product_id is None:
        # Select a random product
        product = random.choice(Product.objects.all())
    else:
        product = get_object_or_404(Product, product_id=product_id)

    # Get recommendations
    recommendations = tfidf_recommendations(product)[:3]  # Get top 3 recommendations

    context = {
        'product': product,
        'recommendations': recommendations,
    }

    return render(request, 'product_detail.html', context)