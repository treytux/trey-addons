# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2016-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Print multiple labels for product variants',
    'summary': 'Print multiple labels for product variants',
    'version': '8.0.0.1.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Product',
    'depends': [
        'product',
        'print_formats_base',
        'web_widget_x2many_2d_matrix',
    ],
    'data': [
        'wizard/print_variant_label_view.xml',
    ],
    'installable': True,
}
