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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

{
    'name': 'agreement_fees',
    'category': 'Account',
    'summary': 'Generate invoices from agreement by fees',
    'version': '8.0.0.1',
    'description': 'Generate invoices from agreement by fees',
    'author': 'Trey (www.trey.es)',
    'depends': [
        'base',
        'account',
        'l10n_es',
        'mail',
        'period',
        'account_payment_partner'
    ],
    'data': [
        'data.xml',
        'views/fees_view.xml',
        'views/menu.xml',
        'wizards/manual_invoice.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [
    ],
    'test': [
        'test/financing.yml',
    ],
    'installable': True,
}
