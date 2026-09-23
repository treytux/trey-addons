###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2024-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Sale order partner shipping empty',
    'category': 'Sales',
    'summary': 'Prevent default shipping addresses in sales orders',
    'version': '16.0.1.0.0',
    'description': 'This module prevents default shipping addresses in sales'
                   ' orders, allowing users belonging to the group Sale Order:'
                   ' Do Not Set Default Shipping Address'
                   ' to control address assignment.',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'depends': [
        'sale_management',
    ],
    'data': [
        'security/security.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
