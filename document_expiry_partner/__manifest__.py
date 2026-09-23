##############################################################################
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
##############################################################################
{
    'name': 'Document Expiry Partner',
    'summary': 'Module to manage partners in document expiry',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Sales',
    'version': '16.0.1.0.0',
    'depends': [
        'contacts',
        'document_expiry',
    ],
    'data': [
        'security/security.xml',
        'data/activity_data.xml',
        'data/cron_data.xml',
        'views/document_expiry_views.xml',
        'views/res_partner_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
