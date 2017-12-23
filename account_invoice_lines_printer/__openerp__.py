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
    'name': 'Invoice Lines Printer',
    'category': 'Account',
    'summary': 'Print Invoice with another lines',
    'version': '8.0.0.1',
    'description': 'Print Invoice with another lines',
    'author': 'Trey (www.trey.es)',
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/invoice_view.xml',
        'views/invoice_report.xml'
    ],
    'installable': True,
}
