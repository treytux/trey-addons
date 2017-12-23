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
    'name': 'Product pricelist rules uom prices',
    'summary': 'Product pricelist rules uom prices',
    'category': 'Product',
    'version': '8.0.0.1',
    'description': """
Update the price of the product in sale order lines according to the selected
unit. This price is obtained from the field 'UoM prices' of the product.
    """,
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'depends': [
        'product',
        'product_pricelist_rules',
        'product_uom_prices',
        'sale_promotion_gift_by_uom'
    ],
    'test': [
        'test/sale_order.yml',
    ],
    'installable': True,
}
