<h2>Product Recommender with LLM Review Summarisation</h2>

<h3>Description:</h3>

This is a demonstration project which does the following:
1. Takes Amazon reviews and product metadata from JSON files
2. Saves these to a database for query efficiency
3. Cleans the data and removes unneeded elements
4. Uses a locally hosted instance of Meta's LLAMA 8B Instruct LLM to generate AI summaries of the reviews,
listing one positive and one negative aspect of each product
5. TODO


Data sources:

Page containing all the data, and a guide on how to use it:
https://cseweb.ucsd.edu/~jmcauley/datasets/amazon/links.html

Home and Kitchen Metadata:
https://snap.stanford.edu/data/amazon/productGraph/categoryFiles/meta_Home_and_Kitchen.json.gz

Home and Kitchen Reviews:
https://snap.stanford.edu/data/amazon/productGraph/categoryFiles/reviews_Home_and_Kitchen.json.gz


Installation:
1. Virtual environment

2. Install Requirements

Running the project:
1. Download data from sources
2. Create a new folder in the root directory
3. Save the data files as gzip in the new folder
4. Run the following base commands to get the data in standard JSON format
5. Run the following base commands to populate the database.