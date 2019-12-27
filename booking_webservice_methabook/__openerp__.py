# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################
{
    'name': 'Booking Webservice Methabook',
    'summary': 'Methabook Booking WebService',
    'description': 'Methabook Booking WebService',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Bookings System',
    'version': '8.0.1.0.0',
    'depends': [
        'account_payment_partner',
        'base',
        'sale',
        'purchase',
        'account',
        'booking_base',
        'booking_webservice',
    ],
    'data': [
        'data/data.xml',
        'data/email_templates.xml',
        'security/ir.model.access.csv',
        'views/booking_line_view.xml',
        'views/booking_view.xml',
        'views/company_view.xml',
        'views/methabook_log.xml',
        'views/partner_view.xml',
        'views/webservice_view.xml',
        'wizard/query_booking_methabook.xml',
    ],
    'installable': True,
}
