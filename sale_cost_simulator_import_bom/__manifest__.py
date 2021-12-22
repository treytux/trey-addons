##############################################################################
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Sale Cost Simulator Import BoM',
    'summary': 'Wizart to import BoM to a simulator cost',
    'description': 'Wizard to import BoM to a simulator cost',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Sale',
    'version': '12.0.1.0.0',
    'depends': [
        'mrp',
        'sale_cost_simulator',
    ],
    'data': [
        'wizards/sale_cost_import_bom_views.xml',
        'views/sale_cost_line_views.xml',
        'views/sale_cost_simulator_views.xml',
    ],
}
