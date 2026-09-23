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
    'name': 'Portal Employee',
    'summary': 'Employee portal tools',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'version': '16.0.1.2.0',
    'depends': [
        'base',
        'document_page',
        'document_page_attachments_management',
        'hr_attendance',
        'hr_holidays',
        'portal',
        'web',
        'website',
    ],
    'data': [
        'data/portal_employee_data.xml',
        'views/document_page_views.xml',
        'views/portal_views.xml',
        'views/res_config_settings.xml',
        'views/res_users_views.xml',
        'views/website_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'portal_employee/static/src/js/portal_employee.js',
        ],
    },
    'images': [
        'static/description/banner.png',
    ],
}
