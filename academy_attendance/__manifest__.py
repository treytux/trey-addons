################################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2024-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Academy Attendance',
    'summary': 'Academy Attendance',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Academy',
    'version': '16.0.1.11.2',
    'depends': [
        'academy',
        'hr_holidays_public',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/ir_sequence_data.xml',
        'reports/report_academy_attendance_sheet.xml',
        'reports/report_academy_teacher_attendance.xml',
        'security/academy_attendance_security.xml',
        'wizard/wizard_teacher_attendance_report.xml',
        'views/academy_activity_views.xml',
        'views/academy_attendance_sheet_views.xml',
        'views/academy_attendance_sheet_line_views.xml',
        'views/academy_training_plan_views.xml',
        'views/academy_training_plan_attendance_line_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'academy_attendance/static/src/css/academy_attendance.css',
        ],
    },
    'demo': [
        'demo/demo.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
