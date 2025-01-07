import ijson
import json
import os

from django.core.management.base import BaseCommand
from product_recommender.models import Product


class Command(BaseCommand):
    help = 'Populates the Product table with data from metadata_processed.json'

    def handle(self, *args, **options):
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the relative path to metadata.json
        file_path = os.path.join(script_dir, '..', '..', '..', 'data_files', 'metadata_processed.json')
        print(file_path)

        processed_count = 0  # Initialize a counter for processed items

        with open(file_path, 'r') as f:
            for item in ijson.items(f, 'item', multiple_values=True):
                try:
                    # Check if "Home & Garden" is in the categories list
                    categories = item.get('categories')
                    if categories and any("Home & Garden" in sublist for sublist in categories):
                        product_id = item['asin']

                        Product.objects.update_or_create(
                            product_id=product_id,
                            defaults={
                                'name': item['title'],
                                'image_url': item['imUrl']
                            }
                        )

                        processed_count += 1

                except Exception as e: 
                    print(f"Error processing item: {item}")
                    print(e)

            print(f"Processed {processed_count} items.") 

        # with open(file_path, 'r') as f:
        #     for item in ijson.items(f, 'item', multiple_values=True):
        #         print(item) 