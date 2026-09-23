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
    'name': 'Payment InStore',
    'summary': 'Allow TPV payments with InStore API.',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Sales',
    'version': '16.0.1.1.1',
    'depends': [
        'account',
        'account_payment_mode',
        'payment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/account_payment_method_data.xml',
        'data/instore_error_mapping_data.xml',
        'data/payment_provider_data.xml',
        'views/account_payment_views.xml',
        'views/instore_error_mapping_views.xml',
        'views/payment_provider_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
