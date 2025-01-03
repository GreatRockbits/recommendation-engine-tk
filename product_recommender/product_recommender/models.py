# This file is where you define your data models, 
# which are Python classes that represent database tables.

from django.db import models
from django.conf import settings

class Product(models.Model):
    product_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    image_url = models.CharField(max_length=255)

class Review(models.Model):
    product_id = models.ForeignKey('Product', on_delete=models.CASCADE)
    review_id = models.IntegerField()
    review_title = models.TextField(null=True)
    review_score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    review_text = models.TextField(null=True)
    created_at_unix = models.IntegerField(blank=True, null=True)


class Summary(models.Model):
    product_id = models.ForeignKey('Product', on_delete=models.CASCADE)
    positive_sentiment = models.TextField(null=True)
    negative_sentiment = models.TextField(null=True)
    


