# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2015-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'My Account',
    'summary': 'Website users portal',
    'category': 'website',
    'version': '8.0.0.1',
    'description': """
    """,
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'depends': [
        'mail',
        'root_partner',
        'sale',
        'web_block_portal',
        'website'],
    'data': [
        'templates/website.xml',
        'templates/website_myaccount.xml',
        'views/res_config.xml',
    ],
    'installable': True,
}
