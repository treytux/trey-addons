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
    'name': 'Albaranes a facturar, más información',
    'category': 'stock',
    'summary': 'Extiende la funcionalidad de los albaranes a facturar',
    'version': '8.0.0.1',
    'description': """
En la ficha del cliente se muestra un indicador con los albaranes pendientes
de facturar y el importe del total. Añade una columna con el importe de la
factura a crear en el listado de albaranes a facturar.

En el asistente de facturar albaranes pendientes permite la opcion a unir en
una factura de venta los albaranes de salida junto a sus devoluciones.

    Este modulo tiene depencias de:
    https://github.com/OCA/stock-logistics-workflow.git
    """,
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'account_journal_sequence_sort',
        'base',
        'stock_account',
        'stock_picking_invoice_link',
        'sale_stock'],
    'data': [
        'views/res_partner_view.xml',
        'views/stock.xml',
        'wizards/stock_invoice_onshipping_view.xml'
    ],
    'installable': True,
}
