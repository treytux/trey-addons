###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2025-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Contract Lite',
    'summary': 'Simplified contracts with recurring invoicing by line',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Sales',
    'version': '16.0.1.6.2',
    'depends': [
        'account',
        'analytic',
        'portal',
        'product',
        'sale',
        'sales_team',
    ],
    'data': [
        'data/ir_cron.xml',
        'security/ir.model.access.csv',
        'security/contract_lite_security.xml',
        'views/contract_lite_contract_views.xml',
        'views/contract_lite_line_views.xml',
        'views/contract_lite_menu.xml',
        'views/contract_lite_portal_templates.xml',
    ],
    'demo': [
        'demo/contract_lite_demo.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
