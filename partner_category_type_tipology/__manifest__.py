###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2026-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Partner Category Type Tipology',
    'summary': 'Partner typologies based on contact tags',
    'version': '16.0.1.0.0',
    'category': 'Extra Tools',
    'website': 'https://www.trey.es',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'contacts',
        'product',
    ],
    'data': [
        'data/res_partner_category_data.xml',
        'views/res_partner_category_views.xml',
        'views/res_partner_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
}
