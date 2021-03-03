###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    advance_line_ids = fields.One2many(
        comodel_name='account.invoice.line',
        inverse_name='advance_line_id',
        string='Advance lines')
    advance_line_id = fields.Many2one(
        comodel_name='account.invoice.line',
        string='Advance line')

    @api.multi
    def unlink(self):
        for line in self:
            advance_creator_line = line.advance_line_ids
            if not advance_creator_line:
                continue
            invoice = advance_creator_line.invoice_id
            if invoice.state != 'draft':
                raise UserError(_(
                    'The invoice that created the advance line "%s" must '
                    'be in draft state to remove both advance lines.') % (
                        advance_creator_line.name))
            advance_creator_line.unlink()
            invoice.compute_taxes()
        return super().unlink()
