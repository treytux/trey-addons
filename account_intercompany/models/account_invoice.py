###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def intercompany_get_id(self, record, company):
        if not record:
            return record.id
        if record.company_id == company:
            return record.id
        record_map = record.intercompany_map_ids.filtered(
            lambda r: r.company_id == company)
        return record_map.id if record_map else False

    @api.model
    def intercompany_parse_vals(self, vals):
        if 'company_id' not in vals:
            return vals
        company = self.env['res.company'].browse(vals['company_id'])
        journal_id = vals.get('journal_id', None)
        if journal_id:
            journal = self.env['account.journal'].browse(journal_id)
            vals['journal_id'] = self.intercompany_get_id(journal, company)
        term_id = vals.get('payment_term_id', None)
        if term_id:
            term = self.env['account.payment.term'].browse(term_id)
            vals['payment_term_id'] = self.intercompany_get_id(term, company)
        mode_id = vals.get('payment_mode_id', None)
        if mode_id:
            mode = self.env['account.payment.mode'].browse(mode_id)
            vals['payment_mode_id'] = self.intercompany_get_id(mode, company)
        return vals

    @api.model
    def create(self, vals):
        vals = self.intercompany_parse_vals(vals)
        return super().create(vals)

    @api.multi
    def write(self, vals):
        vals = self.intercompany_parse_vals(vals)
        return super().write(vals)
