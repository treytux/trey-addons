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
    'name': 'Procurement run according to state',
    'summary': 'Procurement run according to state',
    'description': '''
When you run the procurement orders, it checks if the products associated
with them have one of the following states: 'Obsolete' or 'End of lifecycle'
so as not to execute them, that is to say, they will not change to 'Done'
state.''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Warehouse',
    'version': '8.0.0.1.0',
    'depends': ['procurement'],
    'data': [
        'views/procurement_order.xml'
    ],
    'installable': True,
}
