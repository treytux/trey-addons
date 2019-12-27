# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2014-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'print_contract_report',
    'category': 'Report',
    'summary': 'Print contract report',
    'version': '8.0.0.1',
    'description': """
        This module adds the 'Contract Type' field to the contract, so that,
        depending on it, you can print a report or another from an associated
        sale order.
    """,
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'account_analytic_analysis',
        'analytic',
        'sale_service',
        'sale'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        'reports/report_layout.xml',
        'reports/report_contract_1.xml',
        'reports/report_contract_2.xml',
        'reports/report_sale_contract.xml',

        'views/data.xml',

        'views/contract_view.xml',
        'views/analytic_view.xml',
        'views/sale_view.xml',
        'views/partner_view.xml',
        'views/menu.xml',

    ],
    'demo': [
        'demo/demo.xml',
    ],
    'test': [
        'test/print_contract_report.yml',
    ],
    'installable': True,
}
