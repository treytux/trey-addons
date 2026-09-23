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
    'name': 'Sale Order Analytic Account Autocreate',
    'summary': 'Autocreate analytic account when confirming a sale order',
    'description': '''
Adds a setting on the company to autocreate an analytic account for
each sale order upon confirmation, with the sale order name as the
analytic account name.
    ''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Sales',
    'version': '16.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'analytic',
        'sale',
    ],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
