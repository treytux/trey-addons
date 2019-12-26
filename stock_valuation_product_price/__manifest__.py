###############################################################################
#
#    Trey (www.trey.es)
#    Copyright (C) 2019-Today Trey (www.trey.es) <www.trey.es>
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
    'name': 'Stock Valuation Product Price',
    'category': 'Stock',
    'summary': 'Apply a filter to view products price in stock valuation',
    'version': '11.0.1.0.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'stock',
        'stock_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/multicompany.xml',
        'views/stock_valuation_product_price_view.xml',
    ],
    'installable': True,
}
