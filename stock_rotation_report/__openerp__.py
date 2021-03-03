# -*- coding: utf-8 -*-
##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2017-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Stock rotation report',
    'summary': 'Stock rotation report',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Stock',
    'version': '8.0.2.1.0',
    'depends': [
        'purchase',
        'sale',
        'stock_account',
    ],
    'data': [
        'security/security.xml',
        'data/stock_rotation_cron_data.xml',
        'reports/stock_rotation_report_view.xml',
        'security/ir.model.access.csv',
        'views/product_product_views.xml',
        'views/res_company_views.xml',
        'wizards/stock_rotation_view.xml'
    ],
    'installable': True,
}
