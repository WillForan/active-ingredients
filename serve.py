#!/usr/bin/env python3
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

def ingredient_link(name: str, set_func: FunctionType) -> VdomDict:
    """
    returns html element with link to ingredient.
    using set_func to update state
    """
    return html.a(
        {
            "on_click": lambda event: set_func(name),
            "href": "#ingredient=" + name,  # href/url has no meaning (currently)
        },
        name)



@component
def ProductsWithItem(ingredient, set_product):
    prods = con.execute(products_with_ingredient, (ingredient,)).fetchall()
    prod_table = html.table(
        [
            html.tr(
                [
                    html.td(
                        html.a(
                            {
                                "on_click": lambda event: set_product(row[0]),
                                # href/url has no meaning (currently)
                                "href": "#product=" + row[0],
                            },
                            row[0],
                        )
                    )
                ]
            )
            for row in prods
        ]
    )
    return prod_table


@component
def ProductInfo(product, set_ingredient):
    prods = con.execute(product_info_query, (product,)).fetchall()
    prod_table = html.table(
        [html.tr([html.td(ingredient_link(row[0], set_ingredient))]) for row in prods]
    )
    return html.section(html.h1(product), prod_table)


@component
def TopIngredients(change_i):
    items = con.execute(count_ingredients_query).fetchall()
    items_table = html.table(
        [
            html.tr(
                [
                    html.td(ingredient_link(row[0], change_i)),
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

    # closure: function with access to local (App function interal) state variables and functions
    def product_click(product):
        """setting product should clears ingredient and  add to product list"""
        set_ingredient(None)
        set_product(product)
        set_list_products(list_products + [product])

    print(f"# DEBUG: p={product}; i={ingredient}; list: {list_products}")

    # ingredient's product listing takes priority if it exists
    # (cleared when product is picked)
    if ingredient is not None:
        return html.section(
            html.h1(ingredient), ProductsWithItem(ingredient, product_click)
        )
    elif product is not None:
        return html.section(ProductInfo(product, set_ingredient))

    # default state is to show the ingredients in the most products
    else:
        return html.section(
            html.h1("Top Ingredients"), TopIngredients(change_i=set_ingredient)
        )

if __name__ == "__main__":
    run(App)
