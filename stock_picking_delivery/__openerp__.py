# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
{
    'name': 'Stock Picking Delivery',
    'summary': 'Stock Picking Delivery',
    'description': '''
This module allows to generate a delivery from a out stock picking.
A delivery can be accepted or rejected using an email that was sended
to partner.
        ''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Stock',
    'version': '8.0.0.1.0',
    'depends': [
        'mail',
        'stock',
        'website',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_picking_delivery_email_template.xml',
        'data/stock_picking_delivery_email_reminder_template.xml',
        'data/stock_picking_delivery_cron.xml',
        'views/stock_picking_delivery.xml',
        'views/stock_picking.xml',
        'templates/website.xml',
        'templates/stock_picking_delivery.xml',
    ],
    'installable': True,
}
