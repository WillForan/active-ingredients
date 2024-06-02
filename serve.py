#!/usr/bin/env python3
from os import set_inheritable
import sqlite3
from types import FunctionType
from reactpy import component, html, run, hooks
from reactpy.types import VdomDict

con = sqlite3.connect("db.sqlite3")


## sql queries
count_ingredients_query = """
with cnt as (
  select iid, count(*) as n_used
from ingredient_product
group by iid)
select iname, n_used from cnt join ingredient as i on i.rowid=cnt.iid
order by n_used desc
limit 10;
"""

products_with_ingredient = """
select pname
from ingredient_product
join product as p on p.rowid=pid
join ingredient as i on i.rowid=iid
where iname like ?;
"""

product_info_query = """
select iname
from ingredient_product
join product as p on p.rowid=pid
join ingredient as i on i.rowid=iid
where pname like ?;
"""

# list all conflicts -- not implemented
conflicts_query = """
select ing1.iname, ing2.iname, severity, note
from conflicts as c
join ingredient as ing1 on ing1.rowid=i1
join ingredient as ing2 on ing2.rowid=i2
where (ing1.iname like :1 or ing1.iname like :2) and
      (ing2.iname like :1 or ing2.iname like :2);
"""

# ugly hack! cannot use placeholder for 'where in' list
# so use 'qmark_csv' as varialbe like '?,?' if two products to compare
# very slow merge? todo: benchmark?
# TODO: add product where conflicting ingredeint is coming from to output
conflicts_product_list_template = """
with all_i as (
  select iid from ingredient_product ip
  join product p on ip.pid = p.rowid
     and p.pname in ({qmark_csv}) )
select distinct ing1.iname, ing2.iname, severity, note
from conflicts as c
left join all_i ai1 on ai1.iid=c.i1
left join all_i ai2 on ai2.iid=c.i2
join ingredient as ing1 on ing1.rowid=i1
join ingredient as ing2 on ing2.rowid=i2
where ai1.iid is not null and ai2.iid is not null;
"""
# ('topicals-slather-body-serum-P481500','sun-safety-kit-P510911')
# Citric Acid|Retinol


def make_link(name: str, set_func: FunctionType, key: str) -> VdomDict:
    """
    returns html element with link to ingredient.
    using set_func to update state
    key uesd for href anchor part of url (after '#') currently unused
      either "ingredient" or "product"
    """
    return html.a(
        {
            "on_click": lambda event: set_func(name),
            "href": f"#{key}={name}",  # href/url has no meaning (currently)
        },
        name,
    )


@component
def Conflicts(products: list, set_ingredient, product_click):
    # products = ["sun-safety-kit-P510911", "topicals-slather-body-serum-P481500"]
    query = conflicts_product_list_template.format(
        qmark_csv=",".join(["?"] * len(products))
    )
    conflicts = con.execute(query, products).fetchall()
    # ing1, ing2, severity, notes
    table_rows = [
        html.tr(
            [
                html.td(make_link(row[0], set_ingredient, "ingredient")),
                html.td(make_link(row[1], set_ingredient, "ingredient")),
                html.td(row[2]),
                html.td(row[3]),
            ]
        )
        for row in conflicts
    ]
    table = html.table(table_rows)
    return html.section(
        html.h1("Ingredient Conflicts"),
        html.ul([html.li(make_link(p, product_click, "product")) for p in products]), table
    )


@component
def ProductList(products, set_product):
    prod_table = html.table(
        [
            html.tr([html.td(make_link(row[0], set_product, "product"))])
            for row in products
        ]
    )
    return prod_table


@component
def ProductsWithItem(ingredient, set_product):
    prods = con.execute(products_with_ingredient, (ingredient,)).fetchall()
    return ProductList(prods, set_product)


@component
def ProductsSearch(search_text, set_product):
    query = "select * from product where pname like '%'||?||'%';"
    prods = con.execute(query, (search_text,)).fetchall()
    return ProductList(prods, set_product)


@component
def ProductInfo(product, set_ingredient):
    prods = con.execute(product_info_query, (product,)).fetchall()
    prod_table = html.table(
        [
            html.tr([html.td(make_link(row[0], set_ingredient, "ingredient"))])
            for row in prods
        ]
    )
    return html.section(html.h1(product), prod_table)


@component
def TopIngredients(change_i):
    items = con.execute(count_ingredients_query).fetchall()
    items_table = html.table(
        [
            html.tr(
                [
                    html.td(make_link(row[0], change_i, "ingredient")),
                    html.td(row[1]),
                ]
            )
            for row in items
        ]
    )
    return items_table


@component
def App():
    # setup two state vairables to track ingredients and products
    ingredient, set_ingredient = hooks.use_state(None)
    product, set_product = hooks.use_state(None)
    list_products, set_list_products = hooks.use_state([])
    prod_search, set_prod_search = hooks.use_state("")

    # closure: function with access to local (App function interal) state variables and functions
    def product_click(product):
        """setting product should clears ingredient and  add to product list"""
        print(f"DEBUG: setting product to {product}")
        set_prod_search("")
        set_ingredient(None)
        set_product(product)
        set_list_products(list(set(list_products + [product])))

    print(f"# DEBUG: p={product} (search '{prod_search}'); i={ingredient}; list: {list_products}")

    page = [
        html.input(
            {
                "type": "text",
                "placeholder": "product",
                "value": f"{prod_search}",
                "on_change": lambda event: set_prod_search(
                    event["currentTarget"].get("value")
                ),
            }
        ),
        html.input({"type": "text", "placeholder": "ingredient"}),
        html.br(),
    ]

    # always show potential conflicts if we have anything in the product list
    # TODO: add product_list_remove
    if list_products is not None:
        page.append(Conflicts(list_products, set_ingredient, product_click))

    # ingredient's product listing takes priority if it exists
    # (cleared when product is picked)
    if ingredient is not None:
        page.append(
            html.section(
                html.h1(ingredient), ProductsWithItem(ingredient, product_click)
            )
        )
    elif prod_search:
        # NB: forwarding product_click NOT set_product.
        # the former clears the search. otherwise we never get out of the seach display
        page.append(html.section(ProductsSearch(prod_search, product_click)))

    elif product is not None:
        page.append(html.section(ProductInfo(product, set_ingredient)))

    # default state is to show the ingredients in the most products
    else:
        page.append(
            html.section(
                html.h1("Top Ingredients"), TopIngredients(change_i=set_ingredient)
            )
        )
    return html.section(page)


if __name__ == "__main__":
    run(App)
