# A class to generate AI summaries from the reviews in the Review database
# Relies on using a local instance of LLAMA 3.2 3B via Ollama and appropriate hardware
# Designed to run on an NVIDIA RTX 3080ti
# Run by using "python manage.py generate_ai_summaries_v3" in the terminal

from django.core.management.base import BaseCommand
from product_recommender.models import Product, Review, Summary
import ollama
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Generate AI summaries for products in the database"

    def handle(self, *args, **options):
        generator = GenerateAISummaries()
        generator.generate_ai_summaries()

# Initialise the llama model with appropriate parameters
class GenerateAISummaries:

    # constructor method
    def __init__(self):
        # Define global variables
        self.positive_review_sentiment_prompt = "For the following review text, summarise one positive aspect about the product in a single sentence"
        self.negative_review_sentiment_prompt = "For the following review text, summarise one negative aspect about the product in a single sentence"


    def generate_ai_summaries(self):
        """
        Generates AI summaries for all products in the database.
        """
        for product in Product.objects.all():
            try:
                print(product.product_id)
                reviews = Review.objects.filter(product_id_id=product.product_id)
                concatenated_reviews = "\n\n".join([review.review_text for review in reviews])

                positive_summary = self.generate_summary(concatenated_reviews, self.positive_review_sentiment_prompt)
                negative_summary = self.generate_summary(concatenated_reviews, self.negative_review_sentiment_prompt)

                # Create or update Summary object
                product_obj = Product.objects.get(product_id=product.product_id) 
                summary , created = Summary.objects.update_or_create(product_id=product_obj) 
                summary.positive_sentiment = positive_summary
                summary.negative_sentiment = negative_summary
                summary.save()

                logger.info(f"Generated summaries for product ID: {product.product_id}")

            except Exception as e:
                logger.error(f"Failed to generate summaries for product ID: {product.product_id}: {e}")


    def generate_summary(self, reviews_text, prompt):
        """
        Generates a summary using the Ollama model.

        Args:
            reviews_text: The concatenated review text for the product.
            prompt: The prompt for the LLM.

        Returns:
            The generated summary.
        """
        try:
            prompt_plus_reviews = prompt + "\n\n" + reviews_text
            # Stream response
            response = ollama.generate(
                model="llama3.2",  # Specify the model explicitly
                prompt=prompt_plus_reviews, 
                stream=True,
            )
            summary = ""
            for chunk in response:
                data = chunk["response"]
                summary += data
            return summary.strip()

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return None