# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import tools, fields, models


class IntrastatReport(models.Model):
    _name = 'intrastat.report'
    _auto = False
    _order = 'year desc, month desc'

    year = fields.Char(
        string='Year')
    month = fields.Selection(
        selection=[
            ('01', 'January'),
            ('02', 'February'),
            ('03', 'March'),
            ('04', 'April'),
            ('05', 'May'),
            ('06', 'June'),
            ('07', 'July'),
            ('08', 'August'),
            ('09', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December')],
        string='Month')
    date_invoice = fields.Date(
        string='Date invoice')
    partner_country_code = fields.Char(
        string='Partner country code')
    state_code = fields.Char(
        string='State code')
    incoterm_code = fields.Char(
        string='Incoterm code')
    transaction_code = fields.Char(
        string='Transaction code')
    transport_mode = fields.Char(
        string='Transport mode')
    intrastat_code = fields.Char(
        string='Intrastat code')
    product_country_code = fields.Char(
        string='Product country code')
    procedure_code = fields.Char(
        string='Procedure code')
    weight = fields.Float(
        string='Weight')
    amount_company_currency = fields.Float(
        string='Amount')
    supply_units = fields.Float(
        string='Supply units')
    source_document = fields.Char(
        string='Source document')
    ttype = fields.Char(
        string='Type')
    currency = fields.Char(
        string='Currency')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company')

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'intrastat_report')
        cr.execute("""
            CREATE OR REPLACE VIEW intrastat_report AS (
                SELECT
                    MIN(il.id) AS id,
                    ai.date_invoice AS date_invoice,
                    to_char(ai.date_invoice, 'YYYY') AS year,
                    to_char(ai.date_invoice, 'MM') AS month,
                    rc.code AS partner_country_code,
                    ai.number AS source_document,
                    rcs.code AS state_code,
                    si.code AS incoterm_code,
                    it.display_name AS transaction_code,
                    itm.display_name AS transport_mode,
                    hs.local_code AS intrastat_code,
                    rc2.code AS product_country_code,
                    il.procedure_code AS procedure_code,
                    sum(coalesce(il.weight::float, 0)) AS weight,
                    sum(coalesce(il.quantity::float, 0)) AS supply_units,
                    sum(coalesce(il.amount_company_currency::float, 0))
                        AS amount_company_currency,
                    rcu.name as currency,
                    CASE WHEN i.type = 'export'
                        THEN 'Export'
                        ELSE 'Import'
                        END AS ttype,
                    ai.company_id as company_id
                FROM l10n_es_report_intrastat_product_line AS il
                LEFT JOIN l10n_es_report_intrastat_product AS i ON
                    il.parent_id = i.id
                LEFT JOIN account_invoice AS ai ON
                    il.invoice_id = ai.id
                LEFT JOIN res_currency AS rcu ON
                    ai.currency_id = rcu.id
                LEFT JOIN res_country AS rc ON
                    il.partner_country_id = rc.id
                LEFT JOIN res_country AS rc2 ON
                    il.product_origin_country_id = rc2.id
                LEFT JOIN res_country_state AS rcs ON il.state = rcs.id
                LEFT JOIN hs_code AS hs ON il.intrastat_code_id = hs.id
                LEFT JOIN stock_incoterms AS si ON il.incoterm_id = si.id
                LEFT JOIN intrastat_transaction AS it
                    ON il.transaction_code = it.id
                LEFT JOIN intrastat_transport_mode AS itm
                    ON il.transport = itm.id
                GROUP BY rc.code, hs.local_code, rcs.code, si.code,
                it.display_name, itm.display_name, rc2.code, il.procedure_code,
                ai.date_invoice, ai.number, i.type, rcu.name, ai.company_id
                )""")
