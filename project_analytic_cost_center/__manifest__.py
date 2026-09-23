###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2023-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Project Analytic Cost Center',
    'summary': (
        'Add the cost center to projects and tasks, and it will be '
        'transferred to analytical items when are created'
    ),
    'category': 'Project',
    'version': '16.0.1.1.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'account_analytic_cost_center',
        'hr_timesheet',
        'project',
    ],
    'data': [
        'views/account_analytic_line_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
