# A class to generate AI summaries from the reviews in the Review database
# Relies on using a local instance of LLAMA 3.1 8B Instruct and appropriate hardware
# Designed to run on an NVIDIA RTX 3080ti
# Run by using "python manage.py generate_ai_summaries" in the terminal

from django.core.management.base import BaseCommand
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from product_recommender.models import Product, Review, Summary
import logging
from typing import Tuple, Optional
from tqdm import tqdm
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
hf_api_key = os.getenv("HF_API_KEY")

class LLAMASummarizer:
    def __init__(self, model_id: str = "meta-llama/Llama-3.1-8B-Instruct", access_token: str = hf_api_key):
        self.model_id = model_id
        self.access_token = access_token
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.max_input_length = 3584  # Reserve space for generation
        self._initialize_model()

    def _initialize_model(self) -> None:
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, token=self.access_token)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id, 
                token=self.access_token,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto"
            )
            logger.info(f"Model initialized successfully on {self.device}")
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            raise

    def _truncate_reviews(self, reviews_text: str, prompt: str) -> str:
        """Truncate reviews to fit within token limit while preserving prompt."""
        # First tokenize the prompt to know how much space it takes
        prompt_tokens = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
        prompt_length = len(prompt_tokens['input_ids'][0])
        
        # Calculate remaining space for reviews
        max_reviews_length = self.max_input_length - prompt_length
        
        # Tokenize and truncate reviews
        reviews_tokens = self.tokenizer(
            reviews_text,
            truncation=True,
            max_length=max_reviews_length,
            add_special_tokens=False
        )
        
        # Decode back to text
        truncated_reviews = self.tokenizer.decode(reviews_tokens['input_ids'])
        return truncated_reviews

    def _generate_single_summary(self, product_name: str, review_text: str, sentiment_type: str) -> str:
        """Generate either positive or negative summary based on sentiment type."""
        prompt = { #TODO - remove {product_name} to reduce context length
            "positive": f"""Analyze the following customer reviews and provide a single concise sentence of ONLY one of the positive aspects.
                          Focus on features customers liked, benefits they experienced, and things that worked well:""",
            "negative": f"""Analyze the following customer reviews and provide a single concise sentence of ONLY the negative aspects.
                          Focus on customer complaints, issues encountered, and areas for improvement:"""
        }

        try:
            logger.info(f"Generating {sentiment_type} summary for: {product_name}")
            
            # Truncate reviews to fit within token limit while preserving prompt
            truncated_review_text = self._truncate_reviews(review_text, prompt[sentiment_type])
            full_input = prompt[sentiment_type] + truncated_review_text

            inputs = self.tokenizer(
                full_input,
                return_tensors="pt",
                truncation=True,
                max_length=self.max_input_length
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,  # Control output length
                    temperature=0.7,
                    top_p=0.9,
                    num_return_sequences=1,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            summary = self.tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            logger.info(f"Successfully generated {sentiment_type} summary for: {product_name}")
            return summary.strip()

        except Exception as e:
            logger.error(f"Error generating {sentiment_type} summary for {product_name}: {str(e)}")
            return f"Error generating {sentiment_type} summary."

    def generate_summary(self, product: Product) -> Tuple[str, str]:
        """Generate separate positive and negative summaries for a product's reviews."""
        logger.info(f"\nStarting summary generation for product: {product.name}")
        
        reviews = Review.objects.filter(product_id=product.product_id)
        review_count = reviews.count()
        
        if not reviews.exists():
            logger.warning(f"No reviews found for product {product.name}")
            return "No reviews available.", "No reviews available."

        logger.info(f"Found {review_count} reviews for: {product.name}")
        all_review_text = " ".join([review.review_text for review in reviews])
        
        # Generate separate summaries for positive and negative sentiments
        positive_summary = self._generate_single_summary(product.name, all_review_text, "positive")
        negative_summary = self._generate_single_summary(product.name, all_review_text, "negative")

        logger.info(f"Completed summary generation for: {product.name}")
        return positive_summary, negative_summary

class Command(BaseCommand):
    help = 'Generate AI summaries for product reviews using LLAMA'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of products to process in each batch'
        )

    def handle(self, *args, **options):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        try:
            summarizer = LLAMASummarizer()
            products = Product.objects.all()
            total_products = products.count()
            
            logger.info(f"Starting summary generation for {total_products} products")
            
            with tqdm(total=total_products) as pbar:
                for index, product in enumerate(products, 1):
                    positive, negative = summarizer.generate_summary(product)
                    
                    # Write summaries to database
                    Summary.objects.update_or_create(
                        product_id=product,
                        defaults={
                            'positive_sentiment': positive,
                            'negative_sentiment': negative
                        }
                    )
                    
                    logger.info(f"✓ Product {index}/{total_products} completed: {product.name}")
                    logger.info(f"  Positive: {positive}")
                    logger.info(f"  Negative: {negative}")
                    logger.info("-" * 80)
                    
                    pbar.update(1)
                    
            self.stdout.write(self.style.SUCCESS(f'Successfully generated summaries for {total_products} products'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to generate summaries: {str(e)}'))