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
    'name': 'Account invoice apply pricelist',
    'summary': '''Wizard to allow apply pricelist partner to invoice.''',
    'description': '''
        Wizard to allow apply pricelist partner to invoice.
        If the invoice belongs to a customer, the sales pricelist assigned
        will be applied and if the invoice belongs to a supplier, the supplier
        pricelislt will apply.''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Invoicing & Payments',
    'version': '8.0.0.1',
    'depends': [
        'account',
        'purchase'
    ],
    'data': [
        'wizard/apply_pricelist.xml',
    ],
    'installable': True,
}
