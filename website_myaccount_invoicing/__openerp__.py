# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2015-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'MyAccount Invoicing',
    'summary': 'Incluye un apartado de facturación en el área personal de la '
               ' tienda online.',
    'category': 'website',
    'version': '8.0.0.1',
    'description': """
    En este apartado se puede consultar una lista con los pedidos y descargar
    su correspondiente factura.
    """,
    'author': 'Trey Kilobytes de Soluciones (www.trey.es)',
    'website': 'https://www.trey.es',
    'depends': [
        'account',
        'root_partner',
        'website_myaccount'],
    'data': [
        'security/invoicing_security.xml',
        'security/ir.model.access.csv',
        'templates/website_myaccount.xml',
        'templates/website_myaccount_invoicing.xml',
    ],
    'installable': True,
}
