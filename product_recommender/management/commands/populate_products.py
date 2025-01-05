import json

from django.core.management.base import BaseCommand
from product_recommender.models import Product


class Command(BaseCommand):
    help = 'Populates the Product table with data from metadata.json'

    def handle(self, *args, **options):
        with open('metadata.json', 'r') as f:   # 'r' is read mode
            data = json.load(f)

        for item in data:
            # Check if the product belongs to the 'Home & Kitchen' category
            categories = item.get('categories', [])
            if any('Home & Kitchen' in category for category in categories):
                product = Product(
                    product_id=item['asin'],
                    name=item['title'],
                    image_url=item['imUrl']
                )
                product.save()

        self.stdout.write(self.style.SUCCESS('Successfully populated the Product table'))