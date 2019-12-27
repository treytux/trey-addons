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
    'name': 'Stock account create invoice group by uid',
    'summary': 'Stock account create invoice group by uid',
    'description': '''
Allows grouping by user when a draft invoice is created from stock picking. For
this, you should be check the option 'Group by user' in the wizard.
If the users do not match, it will assign it the user that launch the wizard.
''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Account',
    'version': '8.0.1.0.0',
    'depends': [
        'base',
        'stock_account',
        'purchase',
    ],
    'data': [
        'wizards/stock_invoice_onshipping_view.xml',
    ],
    'installable': True,
}
