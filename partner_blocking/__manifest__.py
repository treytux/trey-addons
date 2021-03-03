###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2018-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Partner Blocking',
    'summary': 'Allow to block/unblock partners',
    'category': 'Customer Relationship Management',
    'version': '11.0.2.0.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': ['base', 'mail', 'web'],
    'data': [
        'views/auth_signin_blocking.xml',
        'views/assets.xml',
        'views/res_partner.xml',
        'views/res_users.xml'
    ],
    'demo': [
        'demo/res_partner_demo.xml'
    ],
    'installable': True,
}
