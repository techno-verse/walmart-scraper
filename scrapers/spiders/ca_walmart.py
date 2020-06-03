import scrapy
import json
from scrapers.items import ProductItem
import re


class CaWalmartSpider(scrapy.Spider):
    # Name of the scraper
    name = "ca_walmart"

    # In order to handle multiple branches we will use branch as a CLI argument
    def __init__(self, branch="3106", *args, **kwargs):
        super(CaWalmartSpider, self).__init__(*args, **kwargs)
        # Branch number passed through CLI. default to 3106
        self.branch = branch
        # Base URL to make urls dynamic
        self.base_url = "https://www.walmart.ca"
        allowed_domains = ["walmart.ca"]
        # URL for fruits category
        self.fruits_urls = "{}/en/grocery/fruits-vegetables/fruits/N-3852".format(self.base_url)
        self.image_url = "https://i5.walmartimages.ca"
        # Cookies for configuring store branch. These are the required cookies
        # by Walmart site
        self.cookies = [
            {'name': 'deliveryCatchment', 'value': '1001'},
            {'name': 'defaultNearestStoreId', 'value': '1001'},
            {'name': 'wmt.breakpoint', 'value': 'd'},
            {'name': 'walmart.shippingPostalCode', 'value': 'M9V2G9'},
            {'name': 'walmart.preferredstore', 'value': branch}
        ]

    def start_requests(self):
        # Here we are going to configure cookies to collect data for each Walmart branch
        yield scrapy.Request(url=self.fruits_urls, cookies=self.cookies, callback=self.parse)

    # This method will be used to get number og pages in dropdown
    def parse(self, response):
        pages = response.css('#shelf-pagination > div.select-native > select > option')
        # For each page we will call construct the url and get items for each
        for page in pages:
            url = "{}/page-{}".format(self.fruits_urls, page.attrib['value'])
            yield scrapy.Request(url=url, cookies=self.cookies, callback=self.parse_page)

    # This method will be ued to get item urls for more detailed item data
    def parse_page(self, response):
        html_items = response.css('div > a.product-link::attr(href)').getall()
        for html_item in html_items:
            item_url = "{}{}".format(self.base_url, html_item)
            yield scrapy.Request(item_url, cookies=self.cookies, callback=self.parse_items)

    """
    This method will be used to parse item data. Walmart site has javascript 
    object called "__PRELOADED_STATE__". This object hold a JSON which includes '
    product details like SKU ids, upc, product description ..etc.
    
    We will use SKU id found in JSON object to call another Walmart APU to extract product pricing 
    which is where the pricing data comes from
    """

    def parse_items(self, response):
        # Product object to utilize the pipline
        item = ProductItem()
        item['url'] = response.request.url
        # Regex to extract JSON out of the HTML <script/> tags
        pattern = r'\{.*\:\{.*\:.*\}\}'
        json_data = response.css('body > script:nth-child(2)::text').re_first(pattern)
        # Convert string to JSON
        json_data = json.loads(json_data)

        # The following section will extract product data from the json
        product_id = json_data['product']['item']['id']
        # We need list of SKU to be sent in "scrapy.FormRequest" as from data
        sku_list = json_data['product']['item']['skus']
        # Active SKU id for the current products
        sku_id = json_data['product']['activeSkuId']

        # An SKU object for the product containing SKU details
        sku = json_data['entities']['skus'][sku_id]

        # Description of the product sold by. If product is sold by weight
        # then we use min and max product just like website does
        # else just use the description
        if sku['grocery']['isSoldByWeight']:
            package = "{} x {}{}".format(sku['grocery']['minWeight'], sku['grocery']['maxWeight'],
                                         sku['grocery']['sellQuantityUOM'])
        else:
            package = json_data['product']['item']['description']

        # Name of the product
        name = sku['name']
        # Number of stock for the given SKU
        stock = len(sku['items'])
        # As per requirements we need barcode as a string not list
        barcodes = str(sku['upc']).replace("[", "").replace("]", "").replace("'", "")
        brand = sku['brand']['name']
        # Using regex to remove html tags such as <br>
        description = sku['longDescription']
        cleanr = re.compile('<.*?>')
        description = re.sub(cleanr, '', description)
        # Here we are passing list of categories to format it with |
        categories = self.format_category(sku['categories'])
        # Here we are constructing image url with the base
        image_url = "{}/{}".format(self.image_url, sku['images'][0]['large']['url'])

        # This final section will create ProductItem object sqlite ingestion
        item["sku"] = sku_id
        item["brand"] = brand
        item["name"] = name
        item["description"] = description
        item["package"] = package
        item["image_url"] = image_url
        item["barcodes"] = barcodes.strip()
        item['branch'] = self.branch
        item['stock'] = stock
        item['category'] = categories

        # This line will call REST API to get pricing data which is not available
        # in the HTML or JS source
        products = [{"productId": product_id, "skuIds": sku_list}]

        # This payload is being sent by Walmart website to get price for each product
        payload = {
            'availabilityStoreId': '1001',
            'experience': 'grocery',
            'fsa': 'L1C',
            'lang': 'en',
            'products': json.dumps(products)
        }

        # This will make a form request replicating the UI flow
        # We are also passing item object to store price and store name
        yield scrapy.FormRequest(url="https://www.walmart.ca/api/product-page/price-offer",
                                 formdata=payload,
                                 callback=self.price_data,
                                 meta={'item': item}
                                 )

    # A simple method parsing json response
    def price_data(self, response):
        item = response.meta.get('item')
        json_body = json.loads(response.body)
        # Current price for the given store
        item['price'] = json_body['offers'][item['sku']]['currentPrice']
        # Name of the brand store providing this products
        item['store'] = json_body['offers'][item['sku']]['sellerInfo']['en']
        yield item

    # We will use this method to format categories using concatenation
    def format_category(self, list):
        categories = ""
        for category in list:
            for hierarchy in category['hierarchy']:
                name = hierarchy['displayName']['en']
                categories += name + "|"
        # Remove the trailing |
        categories = categories[:-1]
        return categories
