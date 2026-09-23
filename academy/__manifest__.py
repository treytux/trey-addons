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
    'name': 'Academy',
    'summary': 'Manage Academy',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Academy',
    'version': '16.0.1.26.1',
    'depends': [
        'analytic',
        'hr',
        'mail',
        'partner_contact_birthdate',
        'partner_contact_personal_information_page',
        'print_formats_base',
        'sale',
        'web_widget_x2many_2d_matrix',
    ],
    'data': [
        'security/academy_security.xml',
        'security/ir.model.access.csv',
        'data/academy_data.xml',
        'data/cron_data.xml',
        'reports/report_academy_enrollment.xml',
        'reports/report_academy_marks_bulletin.xml',
        'reports/report_paperformat.xml',
        'wizard/academy_invoice_activities_wizard.xml',
        'wizard/academy_publish_bulletin_lines.xml',
        'wizard/wizard_fill_bulletin_line.xml',
        'wizard/wizard_generate_bulletins.xml',
        'views/academy_academic_training_views.xml',
        'views/academy_activity_views.xml',
        'views/academy_enrollment_views.xml',
        'views/academy_evaluable_concept_mark_views.xml',
        'views/academy_evaluable_concept_views.xml',
        'views/academy_evaluation.xml',
        'views/academy_marks_bulletin.xml',
        'views/academy_training_plan_views.xml',
        'views/academy_typology_views.xml',
        'views/hr_employee_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/menu.xml',
    ],
    'demo': [
        'demo/academy_demo.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
