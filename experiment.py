from bs4 import BeautifulSoup
import json
import itertools
import os.path
import requests
import re


## supporting functoins and variables
def cache_soup(url: str, fname: os.PathLike) -> BeautifulSoup:
    """
    download a page and save html for reading or read file if already exists
    return beatiful soup object of page
    """
    if not os.path.isfile(fname):
        headers = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0'}
        page = requests.get(url, headers=headers)
        if not page.ok:
            raise Exception(f"cannot download {url}; {page.status_code}")
        with open(fname,'w') as f:
            f.write(page.text)
    with open(fname) as f:
        soup = BeautifulSoup(f, 'html.parser')
    return soup

# urls and cache files to test on
EXAMPLES =  {
    "sephora_1": {
        "url": "https://www.sephora.com/product/lotus-youth-preserve-radiance-renewal-night-cream-P440312",
        "fname": "tests/lotus-youth-preserve-radiance-renewal-night-cream.html"},
    "sephora_dimethicone": {
        "url": "https://www.sephora.com/product/P248407",
        "fname": "tests/sephora-dimethicone.html"},

    "ultra-dimethicone": {
        "url": "https://www.ulta.com/p/ultra-repair-cream-xlsImpprod13491031",
        "fname": "tests/ultra-dimethicone.html"},
}


## example sephora page
# the 3rd to last <script> tag hsa id linkStore (and data-comp="PageJSON ")
# this has the active ingredents
soup = cache_soup(**EXAMPLES["sephora_1"])
# fancy dict to arguments '**' syntax. same as
# soup = cache_soup(url=EXAMPLES["sephora_1"]["url"], fname=url=EXAMPLES["sephora_1"]["fname"])
json_element = soup.find_all('script', id="linkStore")
json_text = json_element[0].text.strip()
json_data = json.loads(json_text)

print(json_data.keys()) # page, ssrProps
brand = json_data['page']['product']['productDetails']['brand']['displayName'] # 'fresh'

# each SKU version of a product has it's own ingredients list
# and each is desribed in html (<p> and <span>)
ingredients_per_type = json_data['page']['product']['regularChildSkus']

# NB. spliting on ',' is probably too naive. "ingredient1 (sub1, sub2)" will split funny.
# TODO: replace all commas in each '(.*?)' with ';' ?
# this is a nest list.
ingredients_nested = [[y.strip() for y in BeautifulSoup(x.get('ingredientDesc', ''), 'html.parser').text.split(", ")] for x in ingredients_per_type]

# unnest (flatten) list of list. set removes duplicate (unique entires)
ingredients_flat = set(itertools.chain.from_iterable(ingredients_nested))
print(ingredients_flat)


###
soup_ultra = cache_soup(**EXAMPLES['ultra-dimethicone'])
# extract brand and product name from page title using regexp (regular expression)
page_title = soup_ultra.find("title").text
title_matches = re.match("^ ?(?P<brand>.*?) - (?P<product>.*?) \\|", page_title)
if title_matches is None:
    raise Exception(f"unexpect title ont like 'brand - product': {page_title}")
title_matches.group('brand') # Ultra Repair Cream'
title_matches.group('product') # 'First Aid Beauty'

## get ingrediants folowing the html element wit id "Ingredients"
all_ingredients = soup_ultra.find(id="Ingredients").nextSibling.text
# 'Active Ingredient: Colloidal Oatmeal 0.50%.Inactive Ingredients: Water, Stearic Acid, Glycerin, C12-15 Alkyl Benzoate, Caprylic/Capric Triglyceride, Glyceryl Stearate, Glyceryl Stearate SE, Cetearyl Alcohol, Butyrospermum Parkii (Shea) Butter, Dimethicone, Squalane, Phenoxyethanol, Caprylyl Glycol, Xanthan Gum, Allantoin, Sodium Hydroxide, Disodium EDTA, Chrysanthemum Parthenium (Feverfew) Extract, Camellia Sinensis Leaf Extract, Glycyrrhiza Glabra (Licorice) Root Extract, Ceramide NP, Eucalyptus Globulus Leaf Oil.'
rm_header = re.sub('.?(In)?[Aa]ctive Ingredients?: ?',', ', all_ingredients)
ingredients_list = rm_header.split(", ")
#ingredients_list_noempty = list(filter(lambda x: x, ingredients_list))
ingredients_list_noempty = [x for x in ingredients_list if x]
print(ingredients_list_noempty)
# ['Colloidal Oatmeal 0.50%', 'Water', 'Stearic Acid', 'Glycerin', 'C12-15 Alkyl Benzoate', 'Caprylic/Capric Triglyceride', 'Glyceryl Stearate', 'Glyceryl Stearate SE', 'Cetearyl Alcohol', 'Butyrospermum Parkii (Shea) Butter', 'Dimethicone', 'Squalane', 'Phenoxyethanol', 'Caprylyl Glycol', 'Xanthan Gum', 'Allantoin', 'Sodium Hydroxide', 'Disodium EDTA', 'Chrysanthemum Parthenium (Feverfew) Extract', 'Camellia Sinensis Leaf Extract', 'Glycyrrhiza Glabra (Licorice) Root Extract', 'Ceramide NP', 'Eucalyptus Globulus Leaf Oil.']
