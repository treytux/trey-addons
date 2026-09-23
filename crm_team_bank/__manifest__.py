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
    'name': 'CRM Team Bank',
    'summary': 'Assign bank accounts per sales team and show them on quotes'
    ' and invoices',
    'category': 'CRM',
    'version': '16.0.1.1.0',
    'website': 'https://www.trey.es',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'crm',
        'sale_management',
        'sales_team',
    ],
    'data': [
        'views/crm_team_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'reports/sale_report.xml',
    ],
    'demo': [
        'demo/res_bank_demo.xml',
        'demo/res_partner_bank_demo.xml',
        'demo/crm_team_demo.xml',
        'demo/sale_order_demo.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
