from django.core.management.base import BaseCommand
from product_recommender.models import Product, Review, Summary
from transformers import pipeline
import ollama

class Command(BaseCommand):
    
    def handle(self, *args, **options):

        # ------------------------------------- Get Product ----------------------------------------------
        product_id = "0615391206"
        reviews = Review.objects.filter(product_id_id=product_id)
        print(reviews)
        print(reviews.first().review_text)

        concatenated_reviews = ""
        for review in reviews:
            concatenated_reviews += "\n\n" + review.review_text

        # print(concatenated_reviews)

        print("END GET PRODUCT")


        # ---------------------------------------- AI Summary ------------------------------------------------
        
        prompt_text = "Summarise the following text in one sentence: "
        prompt_plus_reviews = prompt_text + concatenated_reviews
        # prompt_plus_reviews = prompt_plus_reviews[:1000]
        print("PROMPT + REVIEWS TRUNCATED: " + prompt_plus_reviews)


        # generator = pipeline("text-generation", model="meta-llama/Llama-3.2-1B-Instruct", model_kwargs={"quantization_config": {"load_in_8bit": True}})
        # res = generator(
        #     prompt_plus_reviews,
        #     # max_length=330, # limits length of the text the model generates
        #     max_new_tokens=50,
        #     temperature=0.7,
        #     top_p=0.95,
        #     repetition_penalty=1.2,
        #     truncation=True,
        #     num_return_sequences=2
        # )
        # print(res)


        """Experiment notes:
        model: LLAMA 8B Instruct
            parameters: num_return_sequences=2
                This basically repeats what was input. Took a while, but did generate a response.
            parameters: max_length=30, truncation-true, num_return_sequences=2
                This results in a ValueError - doesn't like the max_length of 30, should increase or set max_new_tokens
            parameters: truncation-true, num_return_sequences=2
                This causes the LLM to just repeat back the input
            parameters: truncation=True, num_return_sequences=2, other: prompt+reviews limited to 1000
                This causes the LLM to just repeat back the input
        model: LLAMA 8B
            parameters: max_new_tokens=50, temperature=0.7, top_p=0.95, repetition_penalty=1.2, truncation=True, num_return_sequences=2
                This basically repeats what was input. Was fast though.
        """

# ------------------------------------------------ Ollama ------------------------------------------------------

        print("OLLAMA STARTING")
        response = ollama.generate(model="llama3.2", prompt=prompt_plus_reviews, stream=True)
        # Stream response
        for chunk in response:
            data = chunk["response"]
            print(data, end="")
        print("OLLAMA ENDING")