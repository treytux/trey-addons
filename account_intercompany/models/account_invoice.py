###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def intercompany_get_id(self, record, company):
        if not record:
            return False
        if record.company_id == company:
            return record.id
        record_map = record.intercompany_map_ids.filtered(
            lambda r: r.company_id == company)
        if not record_map:
            raise UserError(_(
                'You must create a mapped for %s "%s" of the company "%s" for '
                'the company "%s"' % (
                    record._description, record.name, record.company_id.name,
                    company.name)))
        return record_map.id if record_map else False

    @api.model
    def intercompany_check_company(self):
        def same_company(field):
            return (
                self[field].company_id == self.company_id
                if self[field] else True)

        self.ensure_one()
        self = self.with_context(ignore_intercompany=True)
        if not same_company('journal_id'):
            self.journal_id = self.intercompany_get_id(
                self.journal_id, self.company_id)
        if not same_company('payment_term_id'):
            self.payment_term_id = self.intercompany_get_id(
                self.payment_term_id, self.company_id)
        if not same_company('payment_mode_id'):
            self.payment_mode_id = self.intercompany_get_id(
                self.payment_mode_id, self.company_id)

    @api.model
    def create(self, vals):
        invoice = self.new(vals)
        invoice.intercompany_check_company()
        vals = invoice._convert_to_write(invoice._cache)
        return super().create(vals)

    @api.multi
    def write(self, vals):
        if self._context.get('ignore_intercompany'):
            return super().write(vals)
        res = super().write(vals)
        for line in self:
            line.intercompany_check_company()
        return res
