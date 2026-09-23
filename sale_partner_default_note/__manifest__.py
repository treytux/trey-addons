###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2025-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Sale Partner Default Note',
    'summary':
        'Add a field in the partner to set a default note that will be '
        'transferred to sales orders',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'website': 'https://www.trey.es',
    'author': 'Trey (www.trey.es)',
    'license': 'LGPL-3',
    'depends': [
        'sale',
    ],
    'data': [
        'views/res_partner_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
