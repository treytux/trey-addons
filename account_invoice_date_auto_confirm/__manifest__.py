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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Account invoice date auto confirm',
    'version': '16.0.1.0.0',
    'category': 'Accounting',
    'summary': (
        'Automatically confirm draft invoices matching the cron run date'
    ),
    'description': (
        'This module adds a scheduled action that searches draft invoices '
        'and confirms them when their invoice date matches the date the '
        'cron runs on, with an optional parameter to also confirm invoices '
        'with a past invoice date.'
    ),
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'data/ir_cron_data.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
