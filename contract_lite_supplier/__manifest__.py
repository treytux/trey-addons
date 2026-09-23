###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2026-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Contract Lite supplier',
    'summary': 'Simplified contracts with recurring invoicing by line',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'version': '16.0.1.1.1',
    'depends': [
        'account',
        'analytic',
        'mail',
        'product',
    ],
    'data': [
        'data/ir_cron.xml',
        'security/contract_lite_supplier_security.xml',
        'security/ir.model.access.csv',
        'views/contract_lite_supplier_contract_views.xml',
        'views/contract_lite_supplier_line_views.xml',
        'views/contract_lite_supplier_menu.xml',
    ],
    'demo': [
        'demo/contract_lite_supplier_demo.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
