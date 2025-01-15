from django.core.management.base import BaseCommand
from product_recommender.models import Product, Review

class Command(BaseCommand):
    help = 'Removes Product entries with no matching reviews.'

    def handle(self, *args, **options):
        # Get all product IDs that have at least one review
        product_ids_with_reviews = Review.objects.values_list('product_id', flat=True).distinct()
        

        # Delete products that are NOT in the above list
        products_to_delete = Product.objects.exclude(product_id__in=product_ids_with_reviews)
        deleted_count, _ = products_to_delete.delete()

        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {deleted_count} products with no reviews.'))