import itertools
import json  # javascript object notation into python dictonary data struct
import math  # for round up 'ceil' function
import os.path
import re  # regular expressions to extract part of strings
import time  # for 'sleep'

import requests  # pull data from internet
from bs4 import BeautifulSoup  # html into tree of pytohn objets


## supporting functoins and variables
def cache_soup(url: str, fname: os.PathLike) -> BeautifulSoup:
    """
    download a page and save html for reading or read file if already exists
    return beatiful soup object of page
    """
    if not os.path.isfile(fname):
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0"
        }
        page = requests.get(url, headers=headers)
        if not page.ok:
            raise Exception(f"cannot download {url}; {page.status_code}")
        with open(fname, "w") as f:
            f.write(page.text)
        time.sleep(2)  #  dont hammer the remove server
    with open(fname) as f:
        soup = BeautifulSoup(f, "html.parser")
    return soup


# urls and cache files to test on
EXAMPLES = {
    "sephora_1": {
        "url": "https://www.sephora.com/product/lotus-youth-preserve-radiance-renewal-night-cream-P440312",
        "fname": "tests/lotus-youth-preserve-radiance-renewal-night-cream.html",
    },
    "sephora_dimethicone": {
        "url": "https://www.sephora.com/product/P248407",
        "fname": "tests/sephora-dimethicone.html",
    },
    "ultra-dimethicone": {
        "url": "https://www.ulta.com/p/ultra-repair-cream-xlsImpprod13491031",
        "fname": "tests/ultra-dimethicone.html",
    },
}


## example sephora page
# the 3rd to last <script> tag hsa id linkStore (and data-comp="PageJSON ")
# this has the active ingredents
soup = cache_soup(**EXAMPLES["sephora_1"])
# fancy dict to arguments '**' syntax. same as
# soup = cache_soup(url=EXAMPLES["sephora_1"]["url"], fname=url=EXAMPLES["sephora_1"]["fname"])
json_element = soup.find_all("script", id="linkStore")
json_text = json_element[0].text.strip()
json_data = json.loads(json_text)

print(json_data.keys())  # page, ssrProps
brand = json_data["page"]["product"]["productDetails"]["brand"][
    "displayName"
]  # 'fresh'

# each SKU version of a product has it's own ingredients list
# and each is desribed in html (<p> and <span>)
ingredients_per_type = json_data["page"]["product"]["regularChildSkus"]

# NB. spliting on ',' is probably too naive. "ingredient1 (sub1, sub2)" will split funny.
# TODO: replace all commas in each '(.*?)' with ';' ?
# this is a nest list.
ingredients_nested = [
    [
        y.strip()
        for y in BeautifulSoup(x.get("ingredientDesc", ""), "html.parser").text.split(
            ", "
        )
    ]
    for x in ingredients_per_type
]

# unnest (flatten) list of list. set removes duplicate (unique entires)
ingredients_flat = set(itertools.chain.from_iterable(ingredients_nested))
print(ingredients_flat)


###
soup_ultra = cache_soup(**EXAMPLES["ultra-dimethicone"])
# extract brand and product name from page title using regexp (regular expression)
page_title = soup_ultra.find("title").text
title_matches = re.match("^ ?(?P<brand>.*?) - (?P<product>.*?) \\|", page_title)
if title_matches is None:
    raise Exception(f"unexpect title ont like 'brand - product': {page_title}")
title_matches.group("brand")  # Ultra Repair Cream'
title_matches.group("product")  # 'First Aid Beauty'

## get ingrediants folowing the html element wit id "Ingredients"
all_ingredients = soup_ultra.find(id="Ingredients").nextSibling.text
# 'Active Ingredient: Colloidal Oatmeal 0.50%.Inactive Ingredients: Water, Stearic Acid, Glycerin, C12-15 Alkyl Benzoate, Caprylic/Capric Triglyceride, Glyceryl Stearate, Glyceryl Stearate SE, Cetearyl Alcohol, Butyrospermum Parkii (Shea) Butter, Dimethicone, Squalane, Phenoxyethanol, Caprylyl Glycol, Xanthan Gum, Allantoin, Sodium Hydroxide, Disodium EDTA, Chrysanthemum Parthenium (Feverfew) Extract, Camellia Sinensis Leaf Extract, Glycyrrhiza Glabra (Licorice) Root Extract, Ceramide NP, Eucalyptus Globulus Leaf Oil.'
rm_header = re.sub(".?(In)?[Aa]ctive Ingredients?: ?", ", ", all_ingredients)
ingredients_list = rm_header.split(", ")
# ingredients_list_noempty = list(filter(lambda x: x, ingredients_list))
ingredients_list_noempty = [x for x in ingredients_list if x]
print(ingredients_list_noempty)
# ['Colloidal Oatmeal 0.50%', 'Water', 'Stearic Acid', 'Glycerin', 'C12-15 Alkyl Benzoate', 'Caprylic/Capric Triglyceride', 'Glyceryl Stearate', 'Glyceryl Stearate SE', 'Cetearyl Alcohol', 'Butyrospermum Parkii (Shea) Butter', 'Dimethicone', 'Squalane', 'Phenoxyethanol', 'Caprylyl Glycol', 'Xanthan Gum', 'Allantoin', 'Sodium Hydroxide', 'Disodium EDTA', 'Chrysanthemum Parthenium (Feverfew) Extract', 'Camellia Sinensis Leaf Extract', 'Glycyrrhiza Glabra (Licorice) Root Extract', 'Ceramide NP', 'Eucalyptus Globulus Leaf Oil.']

## list of all products
url = "https://www.sephora.com/shop/skincare?sortBy=TOP_RATED&currentPage=1"
fname = "cache/saphora/index/1.html"
idx1 = cache_soup(url, fname)
# total_text = idx1.find('p', {'data-at': 'number_of_products'}).text # 2919 Results
# n_total = int(total_text.replace(' Results','')) # 2919

all_paragraphs = " ".join([x.text for x in idx1.find_all("p", string=True)])
totals_match = re.search("([0-9]+)-([0-9]+) of ([0-9]+) Results", all_paragraphs)
cur_end = int(totals_match.group(2))
n_total = int(totals_match.group(3))

pagelist_text = idx1.find("script", id="linkStore").text
pagelist_json = json.loads(pagelist_text)
products_obj_list = pagelist_json["page"]["nthCategory"]["products"]
len(products_obj_list)  # 60


#######  combine
## TODO: this will move into package src/active_ingredients/ files
def extract_skincare_products(page_idx: int) -> list:
    """
    given a index page, fetch and extract all 60 products on that page
    returns list of dictionaries version of products json object
    """
    base_url = "https://www.sephora.com/shop/skincare?sortBy=TOP_RATED&currentPage="
    base_fname = "cache/saphora/index/"
    res_soup = cache_soup(f"{base_url}{page_idx}", base_fname + f"{page_idx}.html")
    pagelist_text = res_soup.find("script", id="linkStore").text
    pagelist_json = json.loads(pagelist_text)
    products_obj_list = pagelist_json["page"]["nthCategory"]["products"]
    return products_obj_list


def cleanup_ingredient(text):
    """
    * remove bullet description
    * strip extra whitespace
    * TODO: stem words? lowercase all? replace known alternatives with canonical version of ingredient name
    """
    text = text.strip()  # " xyz " => "xyz"
    bullet_match = re.search("^-([^:]+):", text)
    if bullet_match:
        text = bullet_match.group(1)
    return text


def extract_ingredients(soup):
    """
    extract json of a given soup version of a saphora product page
    """
    json_element = soup.find("script", id="linkStore")
    json_text = json_element.text.strip()
    json_data = json.loads(json_text)

    # each SKU version of a product has it's own ingredients list
    # and each is desribed in html (<p> and <span>)
    prod_keys = json_data["page"]["product"].keys()
    if "currentSku" in prod_keys:
        sku_key = "currentSku"
        ingredients_html = json_data["page"]["product"][sku_key]["ingredientDesc"]
        return set(
            [
                cleanup_ingredient(x)
                for x in BeautifulSoup(ingredients_html, "html.parser").text.split(", ")
            ]
        )
    else:
        sku_key = "regularChildSkus"
        ingredients_per_type = json_data["page"]["product"][sku_key]

        # NB. spliting on ',' is probably too naive. "ingredient1 (sub1, sub2)" will split funny.
        # TODO: replace all commas in each '(.*?)' with ';' ?
        # this is a nest list.
        ingredients_nested = [
            [
                cleanup_ingredient(y)
                for y in BeautifulSoup(
                    x.get("ingredientDesc", ""), "html.parser"
                ).text.split(", ")
            ]
            for x in ingredients_per_type
        ]

        # unnest (flatten) list of list. set removes duplicate (unique entires)
        ingredients_flat = set(itertools.chain.from_iterable(ingredients_nested))
    return ingredients_flat


def saphora_n_total() -> int:
    """
    extract total results number from a saphora results page
    """

    url = "https://www.sephora.com/shop/skincare?sortBy=TOP_RATED&currentPage=1"
    fname = "cache/saphora/index/1.html"
    idx1 = cache_soup(url, fname)
    # total_text = idx1.find('p', {'data-at': 'number_of_products'}).text # 2919 Results
    # n_total = int(total_text.replace(' Results','')) # 2919

    all_paragraphs = " ".join([x.text for x in idx1.find_all("p", string=True)])
    totals_match = re.search("([0-9]+)-([0-9]+) of ([0-9]+) Results", all_paragraphs)
    if not totals_match:
        raise Exception("saphora results page did not contain text matching total results")
    #cur_end = int(totals_match.group(2))
    n_total = int(totals_match.group(3))
    return n_total

#####  run for all
# build up product list
n_total = saphora_n_total() # 2922
products_obj_list = []
total_pages = math.ceil(n_total / 60)  # 60 at a time, round up
for page_idx in range(1, total_pages + 1):  # range ends before max, so +1
    print(f"# parsingn page {page_idx}")
    products_obj_list += extract_skincare_products(page_idx)
    #break  # don't actually run yet -- remove break to download all

## get product ingredients
# building dictionary like product=>[ingredient1, ingredient2, ...]
# this is a small dataset. should easily fit into memory.
# were it much bigger, might want to insert into db instead of into in-memory dictionary
prod_ingred = dict()
product_error_list = []
for product in products_obj_list:
    product_name = re.search("/product/([^?]+)", product["targetUrl"]).group(1)
    fname = "cache/saphora/products/" + product_name + ".html"
    url = "https://www.sephora.com/product/" + product_name
    soup = cache_soup(url, fname)
    try:
        ingredients = extract_ingredients(soup)
    except Exception as e:
        print(e)
        product_error_list.append(product)
        continue
    prod_ingred[product_name] = ingredients
    # insert product into db, get rowid
    # upsert ingredient + count
    # insert row: ingredient <-> product join table


## connect to database
import sqlite3
con = sqlite3.connect("db.sqlite3")

# quick and dumb way to get all products and ingredients into the db
# NB. db table has option for more info. e.g. product descripton, is ingredient active
#     the data-structure is only storing names.
#     would need to rework to insert extra info
all_prod_names = [(x,) for x in prod_ingred.keys()]; # must be list of tuples for "excute many"

con.executemany("INSERT OR IGNORE into product(pname) VALUES(?);", all_prod_names)

all_ingredients = [ (x,) for x in set(itertools.chain.from_iterable(prod_ingred.values()))]
con.executemany("INSERT OR IGNORE into ingredient(iname) VALUES(?);", all_ingredients)

# populate join table.
# to save space (premature optimization!) we're using id number instead of full name for the join table
for prod_name, ingredients in prod_ingred.items():
    pid = con.execute("select rowid from product where pname= ?;", (prod_name,)).fetchone()[0]
    for ingredient in ingredients:
        iid = con.execute("select rowid from ingredient where iname= ?;", (ingredient,)).fetchone()[0]
        con.execute("INSERT OR IGNORE into ingredient_product(pid,iid) VALUES(?, ?);", (pid, iid))

citric_acid_id = con.execute("select rowid from ingredient where iname='Citric Acid';").fetchone()[0]
retinol_id = con.execute("select rowid from ingredient where iname='Retinol';").fetchone()[0]

con.execute("INSERT into conflicts (i1,i2,severity,note) values (?,?,?,?)",
            (citric_acid_id, retinol_id, 5, "okay if hours apart"))

# push changes to disk and close database connection
con.commit()
con.close()
