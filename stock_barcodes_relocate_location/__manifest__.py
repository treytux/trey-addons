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
    'name': 'Stock barcodes relocate location',
    'summary': 'Relocate complete location with barcode reader',
    'category': 'Stock',
    'version': '16.0.1.0.1',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'barcodes',
        'sale',
        'stock',
        'stock_barcodes',
        'stock_barcodes_internal_transfers',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/stock_barcodes_relocate_location_security.xml',
        'wizards/stock_barcodes_relocate_location.xml',
        'views/stock_picking_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'stock_barcodes_relocate_location/static/src/js/'
            'stock_barcodes_relocate_location.js',
            'stock_barcodes_relocate_location/static/src/js/'
            'stock_barcodes_relocate_location_form.js',
        ],
    },
    'images': [
        'static/description/banner.png',
    ],
}
