# This class creates a base command which takes the file output from clean_reviews_and_write_new_file
# and writes the data to a the database defined in Django's settings.py
# To run this, use "python manage.py populate_reviews" in the CLI
# Note that the file_path can be amended to fit your chosen filename

import os
import ijson
from django.core.management.base import BaseCommand
from ...models import Product, Review

class Command(BaseCommand):
    help = 'Populates the Review table with data from home_and_kitchen_reviews_processed.json, ' \
           'matching reviews to existing ASINs in the Product table.'

    def handle(self, *args, **options):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, '..', '..', '..', 'data_files', 'home_and_kitchen_reviews_processed.json')
        print(file_path)

        processed_count = 0
        existing_asins = set(Product.objects.values_list('product_id', flat=True))  # Get ASINs

        with open(file_path, 'r') as f:
            for review_data in ijson.items(f, 'item'):
                try:
                    asin = review_data.get('asin')

                    # Check if the ASIN exists in your Product database
                    if asin in existing_asins:  
                        Review.objects.create(
                            product_id=Product.objects.get(product_id=asin),  # Get Product object
                            review_id=review_data.get('unixReviewTime'),  # Use unique review ID
                            review_title=review_data.get('summary'),
                            review_username=review_data.get('reviewerName', 'default user'),
                            review_score=int(review_data.get('overall', 1)),  # Default to 1 if missing
                            review_text=review_data.get('reviewText'),
                            created_at_unix=review_data.get('unixReviewTime')
                        )
                        processed_count += 1

                except Exception as e:
                    print(f"Error processing review: {review_data}")
                    print(e)

        print(f"Processed {processed_count} reviews.")