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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Account Move Unpaid Reminder',
    'version': '16.0.1.1.2',
    'category': 'Accounting',
    'summary': (
        'Send email reminders for draft invoices with unpaid reminder flag'
    ),
    'description': (
        'This module sends email reminders to followers of draft invoices '
        'with the unpaid reminder flag set to True.'
    ),
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'mail',
    ],
    'data': [
        'data/ir_actions_server_data.xml',
        'data/ir_cron_data.xml',
        'views/account_move_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
