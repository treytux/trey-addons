# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2016-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Product Brand Invoice Report Group',
    'version': '8.0.0.1',
    'category': 'Product',
    'summary': 'Apply a filter to view products brands in invoice report',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'product_brand',
        'account',
    ],
    'data': [
        'views/account_invoice_report_view.xml',
    ],
    'installable': True,
}
