###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2018-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'summary': 'Dependencies addons for account spanish instance',
    'category': 'Vertical',
    'version': '16.0.1.8.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'account_banking_mandate',
        'account_banking_pain_base',
        'account_banking_sepa_credit_transfer',
        'account_banking_sepa_direct_debit',
        'account_chart_update',
        'account_due_list',
        'account_financial_report',
        'account_fiscal_position_partner_type',
        'account_fiscal_position_vat_check',
        'account_fiscal_year',
        'account_invoice_constraint_chronology',
        'account_invoice_refund_line_selection',
        'account_invoice_tax_required',
        'account_journal_lock_date',
        'account_lock_date_update',
        'account_mass_reconcile',
        'account_move_line_reconcile_manual',
        'account_move_line_tax_editable',
        'account_move_reconcile_forbid_cancel',
        'account_payment_invoice_online_payment_patch',
        'account_payment_mode',
        'account_payment_order',
        'account_payment_partner',
        'account_payment_purchase',
        'account_payment_return_import',
        'account_payment_return',
        'account_payment_sale',
        'account_payment_term_extension',
        'account_qr_code_sepa',
        'account_reconcile_oca',
        'account_sequence',
        'account_statement_base',
        'account_statement_import_base',
        'account_tax_balance',
        'account_usability',
        'base_bank_from_iban',
        'date_range_account',
        'date_range',
        'intrastat_base',
        'l10n_es_account_asset',
        'l10n_es_account_banking_sepa_fsdd',
        'l10n_es_aeat_mod111',
        'l10n_es_aeat_mod115',
        'l10n_es_aeat_mod303',
        'l10n_es_aeat_mod347',
        'l10n_es_aeat_mod349',
        'l10n_es_aeat_mod390',
        'l10n_es_aeat',
        'l10n_es_dua',
        'l10n_es_irnr',
        'l10n_es_mis_report',
        'l10n_es_mis_report',
        'l10n_es_partner',
        'l10n_es_toponyms',
        'l10n_es_vat_book',
        'l10n_es',
        'partner_bank_acc_type_constraint',
        'spreadsheet_dashboard_account',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'application': True,
}
