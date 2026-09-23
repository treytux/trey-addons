################################################################################
#
#    Trey (www.trey.es)
#    Copyright (C) 2025-Today Trey (www.trey.es) <www.trey.es>
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
################################################################################
{
    'name': 'Negative Balance Reminder',
    'version': '16.0.1.4.1',
    'category': 'Tools',
    'summary': 'Followers are notified when balance is negative.',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'mail',
        'project',
        'project_current_balance',
        'project_current_balance_contract_lite',
        'product_template_maintenance',
    ],
    'data': [
        'data/email_template.xml',
        'data/ir_cron_data.xml',
        'views/project_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
