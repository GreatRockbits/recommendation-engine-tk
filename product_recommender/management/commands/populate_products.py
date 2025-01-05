import json
import os

from django.core.management.base import BaseCommand
from product_recommender.models import Product


class Command(BaseCommand):
    help = 'Populates the Product table with data from metadata.json'

    def handle(self, *args, **options):
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__)) 

        # Construct the relative path to metadata.json
        file_path = os.path.join(script_dir, '..', '..', '..', 'data_files', 'metadata.json')

        with open(file_path, 'r') as f:
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