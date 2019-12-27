# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2017-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Education',
    'summary': 'Education',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Education',
    'version': '8.0.1.0.0',
    'depends': [
        'base',
        'mail',
        'print_formats_base',
        'web_widget_x2many_2d_matrix',
    ],
    'data': [
        'security/education_security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/template_user.xml',
        'reports/report_edu_enrollment.xml',
        'reports/report_edu_marks_bulletin.xml',
        'reports/report_paperformat.xml',
        'reports/report_receipt.xml',
        'wizard/wizard_customer_receipt.xml',
        'wizard/wizard_enroll_student.xml',
        'wizard/wizard_fill_subjects.xml',
        'wizard/wizard_marks_bulletin.xml',
        'wizard/wizard_migrate_student.xml',
        'views/edu_academic_training.xml',
        'views/edu_enrollment.xml',
        'views/edu_enrollment_line.xml',
        'views/edu_evaluation.xml',
        'views/edu_marks_bulletin.xml',
        'views/edu_subject.xml',
        'views/edu_training_plan.xml',
        'views/edu_training_plan_classroom.xml',
        'views/edu_training_plan_line.xml',
        'views/edu_training_plan_typology.xml',
        'views/menu.xml',
        'views/res_partner.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
}
