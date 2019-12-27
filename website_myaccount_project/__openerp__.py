# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2015-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'My Account Project',
    'summary': 'Gestión de Proyectos en el área privada de clientes.',
    'category': 'website',
    'version': '8.0.0.1',
    'description': """
    """,
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'depends': [
        'project',
        'website_myaccount',
        # account_analytic_analysis,
        # account_analytic_analysis_recurring_extension,
        # analytic, analytic_user_function, hr_timesheet, hr_timesheet_invoice,
        # hr_timesheet_sheet, project, project_issue
    ],
    'data': [
        # 'security/ir.model.access.csv',
        # 'security/security.xml',
        'templates/website_myaccount.xml',
        'templates/website_myaccount_project.xml'
    ],
    'installable': True,
}
