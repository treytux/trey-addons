###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2017-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Print options sale cost simulator',
    'summary': 'Print options sale cost simulator',
    'category': 'Tools',
    'version': '16.0.1.1.0',
    'description': '''
        Adds a button to the sale cost simulator that opens a wizard to print
        a report according to the selected options.
    ''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'sale_cost_simulator',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_cost_simulator_view.xml',
        'wizards/print_options_sale_cost_simulator.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
