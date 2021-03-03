# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 Domatix Technologies  S.L. (http://www.domatix.com)
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
    'name': 'Product Pack Pos',
    'summary': 'Product pack',
    'category': 'Sales management',
    'version': '8.0.0.1',
    'description': """
    """,
    'author': 'Domatix',
    'website': '',
    'depends': [
        'product_pack',
        'point_of_sale'
    ],
    'data': [
        'views/pos_view.xml',
        'wizards/pack_add.xml'
    ],
    'test': [
    ],
    'installable': True,
}
