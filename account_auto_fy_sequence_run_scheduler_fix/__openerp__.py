# -*- coding: utf-8 -*-
##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2019-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Account auto fy sequence run scheduler fix',
    'summary': 'Account auto fy sequence run scheduler fix',
    'description': '''
When the module 'account_auto_fy_sequence' is installed when executing the
cron 'Run mrp scheduler' it this error ocurrs:
    'The system tried to access to fiscal year sequence without specifying the
    current fiscal year.'
because in the context you do not pass the key 'fiscalyear_id'. This error
occurs in the background and is not displayed in the log or to the user but is
detected because the stock warehouse orderpoint orders are not executed.

This happens because in the call to the 'run_scheduler' function of the cron
'Run mrp scheduler' that key is not passed in the context.

This module fills that key and assigns the corresponding company to work
correctly.

It also filters the sequences so that only those of the user's company are
taken into account.''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Stock',
    'version': '8.0.0.1.0',
    'depends': [
        'account_auto_fy_sequence',
        'procurement',
    ],
    'data': [
        'data/data.xml'
    ],
    'installable': True,
}
