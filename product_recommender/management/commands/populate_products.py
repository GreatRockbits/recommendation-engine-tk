import ijson
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

        batch_size = 1000  # Define the desired batch size
        data = []  # Initialize an empty list to store the batch

        with open(file_path, 'r') as f:
            for item in ijson.items(f, 'item', multiple_values=True):
                data.append(item)  # Add the item to the batch

                if len(data) >= batch_size:
                    self.process_batch(data)  # Process the batch
                    data = []  # Reset the batch list

            # Process any remaining items after the loop
            if data:
                self.process_batch(data)

    def process_batch(self, data):
        for item in data:
            try:
                product_id = item['asin']

                # Check if the product already exists in the database
                if Product.objects.filter(product_id=product_id).exists():
                    continue

                # Check if the product belongs to the 'Home & Kitchen' category
                categories = item.get('categories', [])
                if any('Home & Kitchen' in category for category in categories):
                    product = Product(
                        product_id=product_id,
                        name=item['title'],
                        image_url=item['imUrl']
                    )
                    product.save()

            except Exception as e:  # Catch any errors during processing
                print(f"Error processing item: {item}")
                print(e)