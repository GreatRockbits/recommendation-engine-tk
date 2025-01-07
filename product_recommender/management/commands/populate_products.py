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
                    product_id = item['asin']
                    print(item)

                    # Use update_or_create to handle existing products
                    Product.objects.update_or_create(
                        product_id=product_id,
                        defaults={
                            'name': item['title'],
                            'image_url': item['imUrl']
                        }
                    )

                    processed_count += 1  # Increment the counter

                except Exception as e:  # Catch any errors during processing
                    print(f"Error processing item: {item}")
                    print(e)

        print(f"Processed {processed_count} items.")  # Print the total count
        # with open(file_path, 'r') as f:
        #     for item in ijson.items(f, 'item', multiple_values=True):
        #         print(item) 