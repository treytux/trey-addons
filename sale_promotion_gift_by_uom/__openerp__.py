# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2015-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Sale promotion gift by uom',
    'summary': 'Sale promotion gift by uom',
    'category': 'Sales',
    'version': '8.0.0.1',
    'description': '''
Add the field unit of measure to the item to be applied to the sales order
gifts depending on the unit selected.''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'depends': [
        'sale',
        'product_uom_prices',
        'product_pricelist_rules',
        'sale_pricelist_rules',
        'sale_promotion_gift',
    ],
    'data': [
        'views/product_pricelist.xml',
        'views/sale_promotion_gift.xml',
        'views/product_pricelist_item_offer.xml',
    ],
    'test': [],
    'installable': True,
}
