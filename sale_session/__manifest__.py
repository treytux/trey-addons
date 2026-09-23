##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2024-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
##############################################################################
{
    'name': 'Sale session',
    'summary': 'Manage sale sessions as a point of sale, but with sale orders',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Sales',
    'version': '16.0.1.14.1',
    'depends': [
        'account',
        'account_financial_risk',
        'crm_team_config',
        'mail',
        'print_formats_account_ticket',
        'sale',
        'sale_management',
        'sale_order_line_menu',
        'sale_stock',
    ],
    'data': [
        'security/security.xml',
        'data/ir_sequence.xml',
        'data/mail_template.xml',
        'data/report_paperformat.xml',
        'security/ir.model.access.csv',
        'wizards/account_payment_register.xml',
        'wizards/sale_order_confirm_and_pay.xml',
        'wizards/sale_session_close.xml',
        'wizards/sale_session_payment.xml',
        'wizards/sale_session_validate.xml',
        'wizards/sale_session_wizard_cash_count.xml',
        'views/report_sale_session_ticket.xml',
        'views/account_payment_views.xml',
        'views/sale_order_views.xml',
        'views/sale_session_views.xml',
        'views/sale_session_cash_count_views.xml',
        'views/crm_team_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
