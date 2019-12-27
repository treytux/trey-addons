# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2014-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
###############################################################################

{
    'name': 'Booking Auto Invoice',
    'category': 'Bookings System',
    'summary': 'Booking Automatic Invoice',
    'version': '8.0.0.1',
    'description': """
        This module adds automatic invoice customer and payment support for
        booking Odoo System
    """,
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'sale',
        'purchase',
        'account',
        'booking_base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/booking_view.xml',
        'views/res_company_view.xml',
        'wizard/massive_invoice.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
}
