###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2021-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Delivery Dachser',
    'summary': 'Generates a file with picking information and register '
               'a shipment in Dachser.',
    'category': 'Delivery',
    'version': '12.0.1.3.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'delivery',
        'delivery_package_number',
        'delivery_price_method',
        'delivery_state',
        'product_dimension',
        'stock_delivery_note',
        'stock_picking_batch_extended',
        'stock_picking_batch_delivery_unique',
    ],
    'external_dependencies': {
        'python': ['zeep'],
    },
    'data': [
        'views/delivery_carrier_views.xml',
        'views/stock_picking_batch_views.xml',
        'views/stock_picking_views.xml',
        'wizards/delivery_dachser.xml',
        'wizards/delivery_dachser_stock_picking_batch.xml',
    ],
}
