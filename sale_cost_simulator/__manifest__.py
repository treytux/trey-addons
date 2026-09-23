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
    'name': 'Sale cost simulator',
    'summary': 'Sale cost simulator',
    'category': 'Sale',
    'version': '16.0.1.0.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'mail',
        'print_formats_base',
        'product',
        'sale',
        'uom',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/multicompany.xml',
        'wizards/apply_pricelist.xml',
        'wizards/import_line.xml',
        'data/mail_template.xml',
        'views/sale_cost_line.xml',
        'views/sale_cost_simulator.xml',
        'views/menu.xml',
        'report/report_sale_cost_simulation.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sale_cost_simulator/static/src/scss/sale_cost_simulator.scss',
        ]
    },
    'images': [
        'static/description/banner.png',
    ],
}
