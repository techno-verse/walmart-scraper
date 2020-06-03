

## Introduction
This is a basic Scrapy based ETL framework which will scrape data from walmart website for any given category based on the provided url.

You can read more about Scrapy [here](https://scrapy.org/)

- **Use Case **: Scraping a product department at Walmart Canada's website

The product information is defined by two models (or tables):

### Product
The Product model contains basic product information:

*Product*

- Store
- Barcodes (a list of UPC/EAN barcodes)
- SKU (the product identifier in the store)
- Brand
- Name
- Description
- Package
- Image URL
- Category
- URL

### BranchProduct
The BranchProduct model contains the attributes of a product that are specific for a store's branch. The same product can be available/unavailable or have different prices at different branches.

*BranchProduct*

- Branch
- Product
- Stock
- Price

Both of the models above have been defined in the `models.py` file

## Use Case Description

Walmart offers a very broad selection of products, from breakfast cereals to gym equipment. We will ingest their product information and store it in our database.

The product information we will scape is:

*Product*

- Store `Walmart`
- Barcodes `60538887928`
- SKU `10295446`
- Brand `Great Value`
- Name `Spring Water`
- Description `Convenient and refreshing, Great Value Spring Water is a healthy option...`
- Package `24 x 500ml`
- Image URL `["https://i5.walmartimages.ca/images/Large/887/928/999999-60538887928.jpg", "https://i5.walmartimages.ca/images/Large/089/6_1/400896_1.jpg", "https://i5.walmartimages.ca/images/Large/88_/nft/605388879288_NFT.jpg"]`
- Category `Grocery|Pantry, Household & Pets|Drinks›Water|Bottled Water`
- URL `https://www.walmart.ca/en/ip/great-value-24pk-spring-water/6000143709667`

*BranchProduct*
 - Product `<product_id>`
 - Branch `3124`
 - Stock `426`
 - Price `2.27`

For now, we are only ingesting the [Fruits](https://www.walmart.ca/en/grocery/fruits-vegetables/fruits/N-3852) category.


## To run the scraper please perform the following steps

1. Set up environment
```
# Clone the repo
git clone https://github.com/shreyaspatel7/walmart-scraper.git
cd walmart-scraper/

# Set up virtual env
virtualenv venv --python=python3
. venv/bin/activate

# Install dependencies
pip install -r requirements.txt 
```
2. You will have to run `python database_setup.py` to generate DB models.
3. You will have to  run the Spider with `python -m scrapy crawl ca_walmart -a branch=3106`. Where `branch` is the id of the Walmart store you want to scrap.This will aggregate the sqlite database.


## Code description

**Description:**

This Scrapy crawler will extract data from Walmart based on the passed branch number as an argument.

It includes all the data cleaning and filtering rules as well as pre-configured cookies that were required by default for the website.


**To run the scraping job for multiple stores, simply pass branch id as following** 
`python -m scrapy crawl ca_walmart -a branch=3124
`
`python -m scrapy crawl ca_walmart -a branch=3106
`

 

