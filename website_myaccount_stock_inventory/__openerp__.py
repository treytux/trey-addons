# -*- coding: utf-8 -*-
##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2018-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
##############################################################################
{
    'name': 'MyAccount Stock Inventory',
    'summary': 'Stock inventory list by season',
    'description': 'Stock inventory list by season',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Website',
    'version': '8.0.0.1.0',
    'depends': [
        'print_formats_base',
        'product_season',
        'product_attribute_priority',
        'report',
        'stock',
        'stock_inventory_online',
        'website_myaccount',
        'website_sale_season_by_user',
    ],
    'data': [
        'reports/report_season.xml',
        'templates/website_myaccount.xml',
        'templates/website_myaccount_stock_inventory.xml',
    ],
    'installable': True,
}
