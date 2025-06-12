# Product Recommender with LLM Review Summarisation & Analytics

## Concept:
The objective of this project is twofold:
1.  To generate AI summaries of the reviews of various products
2.  To run a recommendation engine on the AI generated summaries as well as across all review text for each product
    and display the difference in load times.

---
## Description:
This is a demonstration project which does the following:
1.  Takes Amazon reviews and product metadata from JSON files
2.  Saves these to a database for query efficiency
3.  Cleans the data and removes unneeded elements
4.  Uses a locally hosted instance of Meta's LLAMA 3B LLM to generate AI summaries of the reviews,
    listing one positive and one negative aspect of each product
5.  Creates a set of recommended products based on all of the review text data
6.  Creates a set of recommended products based on the AI positive and negative summaries
7.  Records the loading times for each algorithm used for the two recommendation methodologies
8.  Creates charts summarising the effect of each algorithm on page load times

---
## Installation:
1.  Set up a python virtual environment ([https://docs.python.org/3/library/venv.html](https://docs.python.org/3/library/venv.html))
2.  Install Requirements using `"pip install -r /path/to/requirements.txt"` (remove double quotes and amend filepath)
3.  Install a relevant version of Nvidia's CUDA - customised to your hardware ([https://docs.nvidia.com/deeplearning/frameworks/support-matrix/index.html](https://docs.nvidia.com/deeplearning/frameworks/support-matrix/index.html))
4.  Install Ollama: [https://ollama.com/download](https://ollama.com/download)

---
## Running the project:
1.  Download data from sources (see data sources below)
2.  Create a new folder in the root directory (call this `data_files` to not have to change any filepaths in the management commands)
3.  Save the data files as gzip in the new folder
4.  Create a SQLite database by running the following two commands:
    ```
    python manage.py makemigrations
    python manage.py migrate
    ```
5.  Run the following base commands to get the data in standard JSON format:
    ```
    python manage.py clean_metadata_and_write_new_file.py
    python manage.py clean_reviews_and_write_new_file.py
    ```
6.  Run the following base commands to populate the database with products:
    ```
    python manage.py populate_products.py
    python manage.py populate_reviews.py
    ```
7.  Clean up the database to remove any products which don't have reviews, as these are not useful for this project
    ```
    python manage.py remove_products_with_zero_reviews.py
    ```
8.  Launch the command prompt in Windows and type `"ollama run llama3.2"` (remove double quotes, this command may vary depending on where your Ollama
    instance is installed)
9.  Populate the AI review summaries in the database by running:
    ```
    python manage.py generate_ai_summaries_v3.py
    ```
    This will take a very long time - approx. 20 hours on an RTX 3080 ti for ~25,000 products
10. To collect the static files and apply the CSS, run the command:
    ```
    python manage.py collectstatic
    ```
11. To run the project, use the command:
    ```
    python manage.py runserver
    ```
12. Open your browser and go to the development server listed in the terminal

---
## Key Takeaways
1.  AI generated summaries can reduce buying friction, by lowering the barrier to direct information from review sentiment. The user needn't read all the reviews (Source: [https://www.paypal.com/us/brc/article/what-are-ai-aggregated-reviews](https://www.paypal.com/us/brc/article/what-are-ai-aggregated-reviews))
2.  There is a potential for cost savings in compute. There was a notable time saving by using the recommendation algorithm across the AI summaries rather than the raw review text. This was across 5,000 products used in the sample. Note that there is the tradeoff of having to store the AI summaries in the database.

---
## Technologies, Tools & Techniques used:
* Python
* Django
* Bootstrap
* Javascript
* AJAX
* HTML/CSS
* CUDA
* Ollama
* LLAMA 8B Instruct
* Numpy
* Pandas
* Scikit Learn
* SQLite
* Chart.js

---
## Data sources:
Page containing all the data, and a guide on how to use it:
[https://cseweb.ucsd.edu/~jmcauley/datasets/amazon/links.html](https://cseweb.ucsd.edu/~jmcauley/datasets/amazon/links.html)

Home and Kitchen Metadata:
[https://snap.stanford.edu/data/amazon/productGraph/categoryFiles/meta_Home_and_Kitchen.json.gz](https://snap.stanford.edu/data/amazon/productGraph/categoryFiles/meta_Home_and_Kitchen.json.gz)

Home and Kitchen Reviews:
[https://snap.stanford.edu/data/amazon/productGraph/categoryFiles/reviews_Home_and_Kitchen.json.gz](https://snap.stanford.edu/data/amazon/productGraph/categoryFiles/reviews_Home_and_Kitchen.json.gz)

Other datasets to use
[https://github.com/caserec/Datasets-for-Recommender-Systems](https://github.com/caserec/Datasets-for-Recommender-Systems)

---
## Information Sources & Recommended Reading:
* [https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/](https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/)
* [https://huggingface.co/blog/noob_intro_transformers](https://huggingface.co/blog/noob_intro_transformers)
* [https://huggingface.co/docs/transformers/model_doc/auto](https://huggingface.co/docs/transformers/model_doc/auto)
* [https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)
* [https://huggingface.co/docs/transformers/en/llm_tutorial](https://huggingface.co/docs/transformers/en/llm_tutorial)
* [https://www.youtube.com/watch?v=QEaBAZQCtwE](https://www.youtube.com/watch?v=QEaBAZQCtwE)
* [https://medium.com/@manuelescobar-dev/running-llama-3-locally-with-ollama-9881706df7ac](https://medium.com/@manuelescobar-dev/running-llama-3-locally-with-ollama-9881706df7ac)
* [https://replicate.com/blog/how-to-prompt-llama](https://replicate.com/blog/how-to-prompt-llama)
* [https://www.kdnuggets.com/ollama-tutorial-running-llms-locally-made-super-simple](https://www.kdnuggets.com/ollama-tutorial-running-llms-locally-made-super-simple)
* [https://www.kaggle.com/code/ibtesama/getting-started-with-a-movie-recommendation-system/notebook](https://www.kaggle.com/code/ibtesama/getting-started-with-a-movie-recommendation-system/notebook)

---
## Other useful links:
* [https://ollama.com/download/windows](https://ollama.com/download/windows)
* [https://ollama.com/library/llama3.2](https://ollama.com/library/llama3.2)
* [https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/index.html](https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/index.html)
* [https://developer.nvidia.com/cuda-toolkit-archive](https://developer.nvidia.com/cuda-toolkit-archive)
* [https://docs.nvidia.com/deeplearning/frameworks/support-matrix/index.html](https://docs.nvidia.com/deeplearning/frameworks/support-matrix/index.html)
* [https://ollama.com/library/llama3:8b-instruct-q8_0](https://ollama.com/library/llama3:8b-instruct-q8_0)