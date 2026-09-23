###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.multi
    def create_invoices(self):
        sale_orders = self.env['sale.order'].search([
            ('id', 'in', self._context.get('active_ids', [])),
            ('not_invoice', '=', False),
        ])
        if not sale_orders.exists():
            raise exceptions.ValidationError(_(
                'The selected sales order(s) are marked as "Do not invoice", '
                'the wizard will end without taking any action.'))
        self.env.context = dict(self.env.context)
        self.env.context.update({'active_ids': sale_orders.ids})
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        return res
