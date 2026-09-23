################################################################################
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
################################################################################
{
    'name': 'Education Attendance',
    'summary': 'Education Attendance',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Education',
    'version': '12.0.1.3.0',
    'depends': [
        'education',
        'hr_holidays_public',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_data.xml',
        'data/data.xml',
        'data/student_attendance_mail_data.xml',
        'reports/report_edu_attendance_sheet.xml',
        'reports/report_edu_teacher_attendance.xml',
        'security/education_attendance_security.xml',
        'security/ir.model.access.csv',
        'wizard/wizard_teacher_attendance_report.xml',
        'views/edu_attendance_sheet.xml',
        'views/edu_attendance_sheet_line.xml',
        'views/edu_training_plan.xml',
        'views/edu_training_plan_attendance_line.xml',
        'views/edu_training_plan_line.xml',
        'views/menu.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
