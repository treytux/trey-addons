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
    'name': 'Incoterms Invoice',
    'category': 'Stock',
    'summary': 'Incoterms concepts in Invoice',
    'version': '8.0.0.1',
    'description': 'Add concepts with fret o insurance in customer invoice',
    'author': 'Trey Kilobytes de Soluciones (www.trey.es)',
    'depends': [
        'stock',
        'account',
        'stock_incoterm_extension',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_view.xml',
        'views/account_invoice_view.xml',
    ],
    'installable': True,
}
