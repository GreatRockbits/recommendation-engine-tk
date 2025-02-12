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

        # log which products have been processed
        with open('processed_products.txt', 'w') as f:
            f.write('')  # Empty the file

        generator = GenerateAISummaries()
        generator.generate_ai_summaries()

# Initialise the llama model with appropriate parameters
class GenerateAISummaries:

    # constructor method
    def __init__(self):
        # Define global variables
        self.positive_review_sentiment_prompt = """You are a precise review analyzer. Your responses must:
                                                    1. Be EXACTLY one sentence
                                                    2. Focus ONLY on positive aspects
                                                    3. Never include greetings or additional commentary
                                                    4. Never make suggestions or recommendations
                                                    5. Never include cons or overall assessment"""
        self.negative_review_sentiment_prompt = """You are a precise review analyzer. Your responses must:
                                                    1. Be EXACTLY one sentence
                                                    2. Focus ONLY on negative aspects
                                                    3. Never include greetings or additional commentary
                                                    4. Never make suggestions or recommendations
                                                    5. Never include pros or overall assessment"""


    def log_processed_product(self, product_id, success=True):
        """
        Logs processed product IDs to a file with their status.
        
        Args:
            product_id: The ID of the processed product
            success: Boolean indicating if processing was successful
        """
        status = "SUCCESS" if success else "FAILED"
        with open('processed_products.txt', 'a') as f:
            f.write(f"{product_id}: {status}\n")


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
                summary, created = Summary.objects.update_or_create(
                    product_id=product_obj,
                    defaults={
                        'positive_sentiment': positive_summary,
                        'negative_sentiment': negative_summary,
                    }
                )
                summary.positive_sentiment = positive_summary
                summary.negative_sentiment = negative_summary
                summary.save()

                logger.info(f"Generated summaries for product ID: {product.product_id}")
                self.log_processed_product(product.product_id)

            except Exception as e:
                logger.error(f"Failed to generate summaries for product ID: {product.product_id}: {e}")
                self.log_processed_product(product.product_id, success=False)

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
            prompt_plus_reviews = f"{prompt}\n\nREVIEW TEXT:\n{reviews_text}\n\n"
            # Stream response
            response = ollama.generate(
                model="llama3.2",  # Specify the model explicitly
                prompt=prompt_plus_reviews, 
                stream=True,
                options={
                    "max_tokens": 10  # Adjust the output tokens
                }
            )
            summary = ""
            for chunk in response:
                data = chunk["response"]
                summary += data
            return summary.strip()

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return None