##############################################################################
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
##############################################################################
{
    'name': 'Procurement group warehouse by condition',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Stock',
    'version': '16.0.1.3.3',
    'depends': [
        'purchase_stock',
        'sale',
        'sale_management',
        'stock',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/res_company_views.xml',
        'views/res_config_settings_views.xml',
        'views/stock_warehouse_views.xml',
        'views/procurement_group_warehouse_by_condition_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
