###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2025-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Stock barcodes internal transfers',
    'summary': 'Internal transfers with barcode reader',
    'category': 'Stock',
    'version': '16.0.1.0.3',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'barcodes',
        'sale',
        'stock',
        'stock_barcodes',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/stock_barcodes_internal_transfers.xml',
        'views/stock_picking_type_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'stock_barcodes_internal_transfers/static/src/js/'
            'stock_qty_info_internal_transfers.js',
            'stock_barcodes_internal_transfers/static/src/xml/'
            'stock_qty_info_widget.xml',
            'stock_barcodes_internal_transfers/static/src/js/'
            'stock_barcodes_internal_transfers.js',
            'stock_barcodes_internal_transfers/static/src/js/'
            'stock_barcodes_internal_transfers_form.js',
            'stock_barcodes_internal_transfers/static/src/js/'
            'stock_barcodes_internal_transfers_basic.js',
        ],
    },
    'images': [
        'static/description/banner.png',
    ],
}
