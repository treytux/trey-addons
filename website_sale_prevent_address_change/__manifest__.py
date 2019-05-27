###############################################################################
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
###############################################################################
{
    'name': 'Website Sale Prevent Address Change',
    'category': 'website',
    'summary': '''
Prevent external users from adding or modifying addresses
''',
    'version': '11.0.1.0.0',
    'author': 'Trey (www.trey.es)',
    'depends': [
        'base',
        'portal',
        'website_sale',
    ],
    'data': [
        'templates/portal.xml',
        'templates/website_sale.xml',
    ],
    'installable': True,
}
