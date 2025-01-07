# This file is where you define your data models, 
# which are Python classes that represent database tables.

from django.db import models
from django.conf import settings

# All of the products in the Home & Kitchen category
class Product(models.Model):
    product_id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    image_url = models.CharField(max_length=255)
    price = models.IntegerField(null=True)

# All of the reviews for the products in the Home & Kitchen category
class Review(models.Model):
    product_id = models.ForeignKey('Product', on_delete=models.CASCADE)
    review_id = models.IntegerField()
    review_title = models.TextField(null=True)
    review_score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    review_text = models.TextField(null=True)
    created_at_unix = models.IntegerField(blank=True, null=True)

# House the AI summaries of the reviews and allocate to their relevant products including 
class Summary(models.Model):
    product_id = models.ForeignKey('Product', on_delete=models.CASCADE)
    positive_sentiment = models.TextField(null=True)
    negative_sentiment = models.TextField(null=True)
    
# House whether the recommended product was a good one or not
class Feedback(models.Model):
    initial_product_id = models.ForeignKey('Product', on_delete=models.CASCADE)
    recommended_product_id = models.IntegerField(primary_key=True)
    good_recommendation = models.BooleanField()
    created_at_unix = models.IntegerField(blank=True, null=True)