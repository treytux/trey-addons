# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################
{
    'name': 'Stock picking delivery form',
    'summary': 'Generate a report with information of delivery',
    'description': 'This report show all picking for a delivery for reception',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Warehouse',
    'version': '8.0.1.0.0',
    'depends': [
        'base',
        'delivery',
        'print_formats_base',
        'root_partner',
        'stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'reports/delivery_carrier_collect.xml',
        'views/delivery_carrier.xml',
        'views/stock_picking_delivery_view.xml',
        'views/stock_picking_view.xml',
        'wizards/delivery_carrier_collect_export_csv.xml'
    ],
    'installable': True,
}
