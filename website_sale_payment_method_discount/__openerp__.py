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
    'name': 'Website Sale Payment Method Discount',
    'category': 'website',
    'summary': 'Allows to add discounts according to the'
               ' payment method selected in the store.',
    'version': ' 8.0.1.0.0',
    'author': 'Trey (www.trey.es)',
    'depends': [
        'account',
        'portal',
        'product',
        'sale',
        'sale_discount',
        'website_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'templates/website.xml',
        'templates/website_sale_payment.xml',
        'views/payment_acquire.xml',
    ],
    'installable': True,
}
