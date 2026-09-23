##############################################################################
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
##############################################################################
{
    'name': 'Project task sale order stock',
    'summary': 'Create sales orders from task timesheets and materials',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Project',
    'version': '16.0.1.0.0',
    'depends': [
        'hr_timesheet',
        'project_task_material',
        'sale_stock',
        'sale_timesheet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/project_task_views.xml',
        'views/project_task_material_views.xml',
        'wizards/create_project_task_views.xml',
        'wizards/project_task_create_sale_order_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
