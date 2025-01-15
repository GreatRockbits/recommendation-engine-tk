# This class creates a base command which takes the file output from clean_metadata_and_write_new_file
# and writes the data to a the database defined in Django's settings.py
# To run this, use "python manage.py populate_products" in the CLI
# Note that the file_path can be amended to fit your chosen filename

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
        skip_count = 0

        with open(file_path, 'r') as f:
            for item in ijson.items(f, 'item'):
                try:
                    if 'title' not in item:
                        print(f"Skipping item without title: {item['asin']}") 
                        skip_count += 1
                        continue  # Skip to the next item
                    
                    # Check if "Home & Garden" is in the categories list
                    categories = item.get('categories')
                    if categories and any("Home & Kitchen" in sublist for sublist in categories):

                        product_id = item.get('asin')
                        price = item.get('price')

                        Product.objects.update_or_create(
                            product_id=product_id,
                            defaults={
                                'name': item.get('title'),  # Use .get() for safety
                                'image_url': item.get('imUrl'),
                                'price': price,
                            }
                        )

                        processed_count += 1

                except Exception as e: 
                    print(f"Error processing item: {item}")
                    print(e)

        print(f"Processed {processed_count} items.") 
        print(f"Skipped {skip_count} items.") 

        # with open(file_path, 'r') as f:
        #     for item in ijson.items(f, 'item', multiple_values=True):
        #         print(item) 