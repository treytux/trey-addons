###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2022-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Web view calendar day',
    'summary': 'Add new calendar day view type',
    'category': 'Tools',
    'version': '12.0.2.11.1',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'analytic',
        'event',
        'event_multiple_addresses',
        'hr_holidays_public',
        'project_event',
        'web',
    ],
    'data': [
        'views/account_analytic_account_views.xml',
        'views/event_event_views.xml',
        'views/res_partner_views.xml',
        'views/web_views.xml',
        'wizards/wizard_calendar_event_template.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
