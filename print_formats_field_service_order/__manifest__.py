###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2022-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Print Formats Field Service Order',
    'summary': 'FSM report customization',
    'version': '12.0.1.1.0',
    'category': 'Field Service',
    'website': 'https://www.trey.es',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'fieldservice',
        'print_formats_base',
    ],
    'data': [
        'views/report_fsm_order.xml',
    ],
    'application': True,
}
