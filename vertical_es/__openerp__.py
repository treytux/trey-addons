# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2016-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Vertical Spain',
    'category': 'Vertical',
    'summary': 'Dependencies addons for account spanish instance',
    'version': '8.0.0.1.0',
    'description': '',
    'author': 'Trey (www.trey.es)',
    'depends': [
        # 'account_ignvoice_export_xls',  # Rama de factor libre
        # 'l10n_es_intrastat_product',  # no mergeado
        # 'l10n_es_patch_country_aeat_mod349',  # desconocido
        'account_balance_reporting_xls',
        'account_banking_mandate',
        'account_banking_pain_base',
        'account_banking_payment_export',
        'account_banking_sepa_credit_transfer',
        'account_banking_sepa_direct_debit',
        'account_cancel',
        'account_direct_debit',
        'account_due_list',
        'account_financial_report_webkit_xls',
        'account_followup',
        'account_invoice_constraint_chronology',
        'account_invoice_not_negative',
        'account_journal_active',
        'account_move_line_tree_without_selectors',
        'account_partner_ledger_report',
        'account_payment_partner',
        'account_payment_purchase',
        'account_payment_return',
        'account_payment_return_import_sepa_pain',
        'account_payment_sale',
        'account_payment_sale_stock',
        # 'account_reconcile_trace',  # Problema query en Naparbier
        'account_renumber',
        'account_report_security',
        'account_tax_analysis',
        'account_tax_chart_interval',
        'l10n_es',
        'l10n_es_account_asset',
        'l10n_es_account_balance_report',
        'l10n_es_account_bank_statement_import_n43',
        'l10n_es_account_invoice_sequence',
        'l10n_es_aeat',
        'l10n_es_aeat_mod111',
        'l10n_es_aeat_mod115',
        'l10n_es_aeat_mod303',
        'l10n_es_aeat_mod340',
        'l10n_es_aeat_mod347',
        'l10n_es_aeat_mod349',
        'l10n_es_dua',
        'l10n_es_fiscal_year_closing',
        'l10n_es_partner',
        'l10n_es_toponyms',
        'purchase_fiscal_position_update',
    ],
    'data': [
    ],
    'application': True,
    'installable': True,
}
