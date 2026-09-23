###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError


class ChangePurchaseDiscountWizard(models.TransientModel):
    _name = 'change.purchase.discount.wizard'
    _description = 'Wizard to change discount in a purchase line'

    discount = fields.Float(
        string='New discount (%)',
        default=0.0,
    )

    @api.multi
    def apply_discount(self):
        self.ensure_one()
        purchase_order = self.env['purchase.order'].browse(
            self.env.context.get('active_id')
        )
        if purchase_order.state != 'draft':
            raise UserError(
                'This discount cannot be modified '
                'because the order is confirmed.'
            )
        if not (0.0 <= self.discount <= 100.0):
            raise UserError('The discount must be between 0% and 100%.')
        for line in purchase_order.order_line:
            line.discount = self.discount
