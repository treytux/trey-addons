###############################################################################
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
###############################################################################
{
    'name': 'Custom Website Event Registration Error',
    'summary': 'Changes error message caused by multiple registration '
               'per partner for an event',
    'version': '16.0.1.2.0',
    'category': 'Marketing',
    'website': 'https://github.com/OCA/event',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'event_registration_partner_unique',
        'website',
        'website_event',
    ],
    'data': [
        'data/event_registration_template.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
