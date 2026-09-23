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
    'name': 'Vending Machine',
    'summary': 'Vending Machine Management',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Sale',
    'version': '12.0.1.5.1',
    'depends': [
        'sale',
        'stock',
        'stock_deposit',
    ],
    'data': [
        'data/res_groups.xml',
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'data/ir_config_parameter.xml',
        'views/sale_order_views.xml',
        'views/vending_machine_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'wizards/vending_machine_stock.xml',
        'wizards/vending_machine_move_stock_deposit.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
