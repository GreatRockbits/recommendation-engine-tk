"""
URL configuration for product_recommender project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.homepage, name='homepage'),
    path('search/', views.search_results, name='search_results'),
    path('random/', views.random_product, name='random_product'),
    path('product/<str:product_id>/', views.product_detail, name='product_detail'),
    path('analytics/', views.recommendation_analytics, name='recommendation_analytics'),
    
    # Primary API endpoints (new unified structure)
    path('api/recommendations/<str:product_id>/', views.api_recommendations_both, name='api_recommendations_both'),
    path('api/reviews/<str:product_id>/', views.api_reviews, name='api_reviews'),
    
    # Legacy API endpoints (deprecated - keep for backward compatibility)
    # These can be removed once frontend is fully migrated
    # path('api/recommendations/summary/<str:product_id>/', views.api_recommendations_summary, name='api_recommendations_summary_legacy'),
    # path('api/recommendations/reviews/<str:product_id>/', views.api_recommendations_reviews, name='api_recommendations_reviews_legacy'),
    
    # Optional: Admin/utility endpoints
    # path('admin/cleanup-performance/', views.cleanup_duplicate_performance_records, name='cleanup_performance'),
]