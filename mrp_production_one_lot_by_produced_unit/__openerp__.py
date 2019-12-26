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
    'name': 'Mrp production one lot by produced unit',
    'summary': 'Mrp production one lot by produced unit',
    'description': '''
This module modifies the operation of the manufacturing so that, if a
production lot is introduced for the product to be manufactured, instead of
creating a move with that same production lot, a move is created for each unit
and an unique production lot is assigned to it, it is created from the name of
the selected production lot by adding an incremental sequence. In this way
each manufactured product will have a unique lot.

If the quantity to be manufactured contains decimals, a move will be made per
unit assigning a single lot to each one less the last one that will have as a
quantity one unit plus the decimal part, also with a single lot.''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Manufacturing',
    'version': '8.0.1.0.0',
    'depends': [
        'mrp',
    ],
    'data': [
        'views/mrp_product_produce.xml',
    ],
    'installable': True,
}
