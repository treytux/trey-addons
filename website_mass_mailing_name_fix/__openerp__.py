# -*- coding: utf-8 -*-
##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2019-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Website mass mailing name fix',
    'summary': 'Website mass mailing name fix',
    'description': '''
Avoid the error:

    "object unbound" while evaluating
    'request.registry.test_cr'

    <class 'openerp.addons.base.ir.ir_qweb.QWebException'>,"object unbound"
    while evaluating
    'request.registry.test_cr',<traceback object at 0x7fa73103f2d8>

when you print a qweb report because it loads the assets and does not find the
condition "request.registry.test_cr" used in the module
"website_mass_mailing_name".''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Website',
    'version': '8.0.1.0.0',
    'depends': ['website_mass_mailing_name'],
    'data': [
        'views/assets.xml',
    ],
    'installable': True,
}
