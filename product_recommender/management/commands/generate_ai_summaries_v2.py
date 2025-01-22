# A class to generate AI summaries from the reviews in the Review database
# Relies on using a local instance of LLAMA 3.1 8B Instruct and appropriate hardware
# Designed to run on an NVIDIA RTX 3080ti
# Run by using "python manage.py generate_ai_summaries" in the terminal

from django.core.management.base import BaseCommand
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from product_recommender.models import Product, Review, Summary
import logging
from typing import Tuple
from tqdm import tqdm
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
hf_api_key = os.getenv("HF_API_KEY")



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

class generateAISummaries:

    # constructor method
    def __init__(self):
        # Define global variables
        self.positive_review_sentiment_prompt = "For the following review text, summarise one positive aspect about the product in a single sentence"
        self.negative_review_sentiment_prompt = "For the following review text, summarise one negative aspect about the product in a single sentence"
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

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id, 
                device_map="auto",
                load_in_4bit=True
            )

            logger.info(f"Model initialized successfully on {self.device}")

        except Exception as e:
                logger.error(f"Failed to initialize model: {str(e)}")
                raise

    # get reviews for a single product based on its product_id and concatenate
    def concatenate_reviews(product_id) -> str:
        # initialise string
        concatenated_reviews = ""
        try:
            # get reviews for this product_id
            reviews = Review.objects.filter(product_id=Product.product_id)
            logger.info(f"successfully concatenated for {product_id}, length: " + len({concatenated_reviews}))
            
            # concatenate found reviews
            for review in reviews:
                concatenated_reviews += review

        except Exception as e:
            logger.error(f"couldn't return reviews for ASIN: {product_id}")

        return concatenated_reviews
        
    # tokenize the prompt and review text, and ensure it meets max input token criterion
    def tokenize_and_truncate(self, review_text, prompt):

        # tokenize the prompt, and get its length
        tokenized_prompt = self.tokenizer.tokenize(
            prompt, 
            add_special_tokens=False
        )
        tokenized_prompt_length = len(tokenized_prompt)

        # find the max length the review can be tokenized to and truncate the review tokens
        max_review_token_length = self.max_input_length - tokenized_prompt_length - 1
        tokenized_reviews = self.tokenizer.tokenize(
            review_text, 
            add_special_tokens=False,
            max_length=max_review_token_length
        )

        return tokenized_reviews

