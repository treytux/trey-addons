###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    def _get_search_domain(self, search, category, attrib_values):
        if not search:
            return super()._get_search_domain(
                search=search, category=category, attrib_values=attrib_values)
        domain = request.website.sale_product_domain()
        if search[0] == '"' and search[-1] == '"':
            domain += [('searchable_text', 'ilike', search[1:-1])]
        else:
            search_terms = search.split(' ')
            domain += ['|'] * (len(search_terms) - 1)
            for search_term in search_terms:
                domain += [('searchable_text', 'ilike', search_term)]
        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]
        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]
        return domain
