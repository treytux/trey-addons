# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2020-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Bookings Invoice Summary',
    'category': 'Bookings System',
    'summary': 'Booking Invoice Summary',
    'version': '8.0.1.0.1',
    'description': '''Send Invoice Summary to Clients''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'booking',
        'booking_commission',
    ],
    'data': [
        'data/email_template.xml',
        'security/ir.model.access.csv',
        'views/booking_invoice_summary_view.xml',
        'views/booking_invoice_summary_line_view.xml',
    ],
    'external_dependencies': {
        'python': ['xlsxwriter']
    },
    'installable': True,
}
