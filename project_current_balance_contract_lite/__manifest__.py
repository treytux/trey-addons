################################################################################
#
#    Trey (www.trey.es)
#    Copyright (C) 2026-Today Trey (www.trey.es) <www.trey.es>
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
    'name': 'Project Current Balance Contract Lite',
    'version': '16.0.1.1.0',
    'category': 'Project',
    'summary': 'Contract-based extension for project current balance',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'contract_lite',
        'project_current_balance',
    ],
    'data': [
        'views/project_project_views.xml',
        'views/project_task_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
