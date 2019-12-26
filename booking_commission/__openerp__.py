# -*- coding: utf-8 -*-
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
    'name': 'Bookings commissions',
    'version': '8.0.1.0.0',
    'author': 'Trey (www.trey.es)',
    'category': 'Bookings System',
    'depends': [
        'account',
        'base',
        'booking',
        'booking_webservice_methabook',
        'product',
        'sale',
        'web_widget_one2many_tags',
    ],
    'data': [
        'data/booking_commission_data.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_view.xml',
        'views/booking_commission_view.xml',
        'views/booking_line_agent_view.xml',
        'views/booking_line_view.xml',
        'views/booking_view.xml',
        'views/menu.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/settlement_view.xml',
        'wizard/wizard_invoice.xml',
        'wizard/wizard_settle.xml',
    ],
    'installable': True,
}
