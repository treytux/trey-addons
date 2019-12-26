# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _


class BookingCommissionMakeInvoice(models.TransientModel):
    _name = 'booking.commission.make.invoice'

    def _default_journal(self):
        return self.env['account.journal'].search(
            [('type', '=', 'purchase')])[:1]

    def _default_refund_journal(self):
        return self.env['account.journal'].search(
            [('type', '=', 'purchase_refund')])[:1]

    def _default_settlements(self):
        return self.env.context.get('settlement_ids', [])

    def _default_from_settlement(self):
        return bool(self.env.context.get('settlement_ids'))

    def _default_booking_id(self):
        return self.env.user.company_id.commission_product_id

    journal = fields.Many2one(
        comodel_name='account.journal', required=True,
        domain="[('type', '=', 'purchase')]",
        default=_default_journal,
    )
    refund_journal = fields.Many2one(
        string='Refund Journal',
        comodel_name='account.journal', required=True,
        domain="[('type', '=', 'purchase_refund')]",
        default=_default_refund_journal,
    )
    product = fields.Many2one(
        string='Booking for invoicing',
        comodel_name='product.template',
        default=_default_booking_id,
        required=True,
    )
    settlements = fields.Many2many(
        comodel_name='booking.commission.settlement',
        relation="booking_commission_make_invoice_settlement_rel",
        column1='wizard_id',
        column2='settlement_id',
        domain="[('state', '=', 'settled')]",
        default=_default_settlements,
    )
    from_settlement = fields.Boolean(
        default=_default_from_settlement,
    )
    date = fields.Date(
        string='Date',
    )

    @api.multi
    def button_create(self):
        self.ensure_one()
        if not self.settlements:
            settlements = self.env['booking.commission.settlement'].search(
                [('state', '=', 'settled'),
                 ('agent_type', '=', 'agent')])
        else:
            settlements = self.settlements
        settlements.make_invoices(self.journal, self.refund_journal,
                                  self.product, date=self.date)
        if settlements:
            return {
                'name': _('Created Invoices'),
                'type': 'ir.actions.act_window',
                'views': [[False, 'list'], [False, 'form']],
                'res_model': 'account.invoice',
                'domain': [['id', 'in', [x.invoice.id for x in settlements]]]
            }
        else:
            return {'type': 'ir.actions.act_window_close'}
