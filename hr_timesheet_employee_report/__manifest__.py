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
    'name': 'Employee Timesheet Report',
    'summary': 'Sends a report of employee timesheet hours by email.',
    'description': '''
This module generates a report with hours recorded by each
employee in their timesheets, covering the current month and the previous
month. The report is automatically sent by email to configured recipients.
    ''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'version': '16.0.1.2.0',
    'depends': [
        'base',
        'hr_holidays',
        'hr_timesheet',
        'mail',
        'project_task_real_time',
    ],
    'data': [
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'security/hr_timesheet_employee_report_groups.xml',
        'security/ir.model.access.csv',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
