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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

{
    'name': 'Payment Acquirer Payment Mode',
    'summary': 'Modo de Pago para los Métodos de Pago de la tienda online.',
    'category': 'Website',
    'version': '8.0.0.1',
    'description': '''
    Permite indicar que Modo de Pago asignar en la factura para los pedidos de
    la tienda online a partir del Método de Pago utilizado.
    ''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'depends': [
        'account_payment',
        'payment',
        'sale',
        'website',
        'website_sale'
    ],
    'data': [
        'views/payment_acquirer_payment_mode.xml'
    ],
    'test': [
    ],
    'installable': True,
}
