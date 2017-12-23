# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2014-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
###############################################################################

{
    'name': 'Account Invoice Sequencial Dates',
    'summary': 'Invoice with consistent dates',
    'category': 'Account',
    'version': '8.0.0.2',
    'description': 'This module customizes Odoo in order to make '
                   'invoices with consistent dates.',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'depends': [
        'account',
        'l10n_es_account_invoice_sequence'
    ],
    'data': [
        'views/account_invoice_view.xml'
    ],
    'test': [
        'test/invoice_sequential.yml'
    ],
    'active': False,
    'installable': True
}
