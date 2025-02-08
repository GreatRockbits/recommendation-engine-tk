# A class to generate AI summaries from the reviews in the Review database
# Relies on using a local instance of LLAMA 3.1 8B Instruct and appropriate hardware
# Designed to run on an NVIDIA RTX 3080ti
# Run by using "python manage.py generate_ai_summaries" in the terminal

from django.core.management.base import BaseCommand
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from product_recommender.models import Product, Review, Summary
import logging
from typing import Tuple
from tqdm import tqdm
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
hf_api_key = os.getenv("HF_API_KEY")

class Command(BaseCommand):
    help = "Generate AI summaries for products in the database"

    def handle(self, *args, **options):
        generator = GenerateAISummaries()
        generator.generate_ai_summaries()

# Steps:
# 1 - Initialise llama
    # add model
    # add parameters
    # add 
# 2 - Loop through ASIN
# 3 - Find reviews for those ASINs and concatenate
# 4 - Generate positive AI summary by adding prompt and reviews
# 5 - Generate negative AI summary by adding prompt and reviews
# 6 - Write summaries to database
# 7 - Call all of these in a base command    

# Initialise the llama model with appropriate parameters
class GenerateAISummaries:

    # constructor method
    def __init__(self):
        # Define global variables
        self.positive_review_sentiment_prompt = "For the following review text, summarise one positive aspect about the product in a single sentence"
        self.negative_review_sentiment_prompt = "For the following review text, summarise one negative aspect about the product in a single sentence"
        self.tokenized_positive_prompt = None
        self.tokenized_negative_prompt = None
        self.model_id = "meta-llama/Llama-3.1-8B-Instruct"
        self.access_token = os.getenv("HF_API_KEY")
        # self.device = "cuda" if torch.cuda.is_available() else "cpu" # backup for if device_map="auto" doesn't work
        self.max_input_length = 12000  # Reserve space for generation - 3584
        self._initialize_llama()

    # initialize the llama model and assign it to the class
    def _initialize_llama(self) -> None:

        # initialise the tokenizer and the model, using hf access token and appropriate parameters
        # https://huggingface.co/docs/transformers/model_doc/auto
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id, 
                token=self.access_token
            )
            self.tokenizer.pad_token = self.tokenizer.eos_token

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id, 
                device_map="auto",
                load_in_4bit=True
            )

            logger.info(f"Model initialized successfully") # add on "{self.device}" if using self.device in constructor 

            # tokenize the positive and negative prompts
            self.tokenized_positive_prompt = self.tokenizer.tokenize(
                self.positive_review_sentiment_prompt, 
                add_special_tokens=False
                )
            self.tokenized_negative_prompt = self.tokenizer.tokenize(
                self.negative_review_sentiment_prompt, 
                add_special_tokens=False
                )

        except Exception as e:
                logger.error(f"Failed to initialize model: {str(e)}")
                raise

    # get reviews for a single product based on its product_id and concatenate
    def concatenate_reviews(self, product_id) -> str:
        # initialise string
        concatenated_reviews = ""
        try:
            # get reviews for this product_id
            reviews = Review.objects.filter(product_id_id=product_id)
            if not reviews.exists():
                logger.info(f"no reviews found for {product_id}")
            
            # concatenate found reviews
            for review in reviews:
                concatenated_reviews += str(review.review_text)

            logger.info(f"successfully concatenated for {product_id}, length: {len(concatenated_reviews)}")

        except Exception as e:
            logger.error(f"couldn't concatenate reviews for ASIN: {product_id}, stuck at concatenate_reviews because {e}")

        return concatenated_reviews
        
    # tokenize the prompt and review text, and ensure it meets max input token criterion
    def tokenize_and_truncate_reviews(self, tokenized_prompt, review_text):

        try:
            tokenized_prompt_length = len(tokenized_prompt)
            logger.info(f"successfully retrieved length of tokenized prompt")

        except Exception as e:
            logger.error(f"couldn't retrieve length of tokenized prompt")
            return []

        # find the max length the review can be tokenized to and truncate the review tokens
        try:
            max_review_token_length = self.max_input_length - tokenized_prompt_length - 1
            tokenized_reviews = self.tokenizer.tokenize(
                review_text, 
                add_special_tokens=False,
                max_length=max_review_token_length,
                truncation=True
            )
            logger.info(f"successfully truncated reviews")
            return tokenized_reviews
        
        except Exception as e:
            logger.error(f"couldn't truncate reviews")
            return []
        
    # generate a positive summary for a single product
    def generate_positive_summary(self, product_id):
        # take the tokenized reviews, the tokenized prompt and generate the review summary
        try:
            # Step 1: Concatenate reviews for the product
            logger.info(f"Generating positive summary for: {product_id}")
            concatenated_reviews = self.concatenate_reviews(product_id)

            # Step 2: Tokenize and truncate the concatenated reviews
            tokenized_reviews = self.tokenize_and_truncate_reviews(
                self.tokenized_positive_prompt, concatenated_reviews
            )

            if not tokenized_reviews:
                logger.warning(f"Tokenized reviews for {product_id} are empty.")
                return "Positive summary error: Empty tokenized reviews."

            # Step 3: Prepare input for the model (combine prompt and reviews)
            input_ids = self.tokenizer(
                self.positive_review_sentiment_prompt + " " + concatenated_reviews,
                return_tensors="pt",
                max_length=self.max_input_length,
                truncation=True
            )["input_ids"].to(self.model.device)

            # Step 4: Generate a summary
            output = self.model.generate(
                input_ids=input_ids,
                max_new_tokens=100,  # Limit the length of the generated summary
                temperature=0.7,     # Controls creativity
                top_k=50             # Sampling from the top-k tokens
            )

            # Step 5: Decode and return the generated summary
            positive_summary = self.tokenizer.decode(output[0], skip_special_tokens=True)
            logger.info(f"Generated positive summary for {product_id}: {positive_summary}")
            return positive_summary

        except Exception as e:
            logger.error(f"Error generating positive summary for {product_id}: {str(e)}")
            return "Positive summary error"
            
    # generate a negative summary for a single product
    def generate_negative_summary(self, product_id):
        # take the tokenized reviews, the tokenized prompt and generate the review summary
        try:
            # Step 1: Concatenate reviews for the product
            logger.info(f"Generating negative summary for: {product_id}")
            concatenated_reviews = self.concatenate_reviews(product_id)

            # Step 2: Tokenize and truncate the concatenated reviews
            tokenized_reviews = self.tokenize_and_truncate_reviews(
                self.tokenized_negative_prompt, concatenated_reviews
            )

            if not tokenized_reviews:
                logger.warning(f"Tokenized reviews for {product_id} are empty.")
                return "Negative summary error: Empty tokenized reviews."

            # Step 3: Prepare input for the model (combine prompt and reviews)
            input_ids = self.tokenizer(
                self.negative_review_sentiment_prompt + " " + concatenated_reviews,
                return_tensors="pt",       
                max_length=self.max_input_length,
                truncation=True
            )["input_ids"].to(self.model.device)

            # Step 4: Generate a summary
            output = self.model.generate(
                input_ids=input_ids,
                max_new_tokens=100,  # Limit the length of the generated summary
                temperature=0.7,     # Controls creativity
                top_k=50             # Sampling from the top-k tokens
            )

            # Step 5: Decode and return the generated summary
            negative_summary = self.tokenizer.decode(output[0], skip_special_tokens=True)
            logger.info(f"Generated negative summary for {product_id}: {negative_summary}")
            return negative_summary

        except Exception as e:
            logger.error(f"Error generating negative summary for {product_id}: {str(e)}")
            return "Negative summary error"

    # generate AI summaries for all products in the Product table
    def generate_ai_summaries(self):
        """Generate and save AI summaries for all products."""
        products = Product.objects.all()
        for product in tqdm(products, desc="Generating summaries"):
            try:
                concatenated_reviews = self.concatenate_reviews(product.product_id)
                if not concatenated_reviews:
                    logger.warning(f"No reviews found for product {product.product_id}. Skipping.")
                    continue

                # Generate positive and negative summaries
                positive_summary = self.generate_positive_summary(product.product_id)
                negative_summary = self.generate_negative_summary(product.product_id)

                # Save summaries to the database
                summary, created = Summary.objects.get_or_create(product_id=product)
                summary.positive_sentiment = positive_summary
                summary.negative_sentiment = negative_summary
                summary.save()

                logger.info(f"Summaries saved for product {product.product_id}")
            except Exception as e:
                logger.error(f"Error processing product {product.product_id}: {str(e)}")
        