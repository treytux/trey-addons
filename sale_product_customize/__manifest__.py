###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2020-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Sale Product Customize',
    'summary': 'Manage product customizations',
    'category': 'sale',
    'version': '12.0.1.3.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'document',
        'sale',
    ],
    'data': [
        'data/sale_customization_color.xml',
        'data/sale_customization_type.xml',
        'data/sale_customization_position.xml',
        'security/ir.model.access.csv',
        'wizards/sale_customization_add.xml',
        'wizards/sale_customization_add_file.xml',
        'views/assets.xml',
        'views/sale_customization.xml',
        'views/sale_customization_color.xml',
        'views/sale_customization_position.xml',
        'views/sale_customization_type.xml',
        'views/sale_order.xml'
    ],
}
