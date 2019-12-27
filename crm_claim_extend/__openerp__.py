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
    'name': 'Crm claim extend',
    'summary': 'Crm claim extend',
    'category': 'Crm',
    'version': '8.0.0.1',
    'description': '''
    Add functionality to claims:
    - Add field 'date viewer' to indicate when the user has read it.
    - Add relationship between sales order and claims.
    - Hide stages and create a new field 'state' with different functions.
    ''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'depends': [
        'crm',
        'sale'
    ],
    'data': [
        'views/crm_claim_view.xml',
        'views/sale_view.xml',
    ],
    'installable': True,
}
