###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    team_bank_account_ids = fields.Many2many(
        comodel_name='res.partner.bank',
        related='team_id.bank_account_ids',
        string='Recipient Banks',
        readonly=True,
    )
    partner_bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        string='Recipient Bank',
        help='Bank account that will be printed on the quotation report and '
             'copied to the invoice.',
    )

    @api.onchange('team_id')
    def _onchange_team_id_partner_bank(self):
        for order in self:
            allowed = order.team_bank_account_ids
            if order.partner_bank_id and order.partner_bank_id not in allowed:
                order.partner_bank_id = False
            if not order.partner_bank_id and len(allowed) == 1:
                order.partner_bank_id = allowed[0]

    @api.onchange('team_id')
    def _onchange_team_id_team_bank(self):
        self._onchange_team_id_partner_bank()

    @api.constrains('team_id', 'partner_bank_id')
    def _check_partner_bank_is_allowed(self):
        for order in self:
            if not order.partner_bank_id or not order.team_id:
                continue
            if order.partner_bank_id not in order.team_bank_account_ids:
                raise ValidationError(
                    'Selected bank account is not allowed for the chosen '
                    'sales team.'
                )

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        bank = self.partner_bank_id
        if not bank and 'team_bank_id' in self._fields:
            bank = self.team_bank_id
        if bank:
            vals['partner_bank_id'] = bank.id
        return vals

    def _create_invoices(self, grouped=False, final=False, date=None):
        invoices = super()._create_invoices(
            grouped=grouped,
            final=final,
            date=date,
        )
        for inv in invoices.filtered(lambda m: not m.partner_bank_id):
            orders = inv.invoice_line_ids.sale_line_ids.order_id
            orders = orders.filtered(
                lambda o: o.partner_bank_id or (
                    'team_bank_id' in o._fields and o.team_bank_id)
            )
            if orders:
                order = orders[0]
                bank = order.partner_bank_id
                if not bank and 'team_bank_id' in order._fields:
                    bank = order.team_bank_id
                if bank:
                    inv.partner_bank_id = bank
        return invoices
