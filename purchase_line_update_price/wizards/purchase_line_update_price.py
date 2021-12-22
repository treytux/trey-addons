###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class PurchaseLineUpdatePrice(models.TransientModel):
    _name = 'purchase.line.update.price'
    _description = 'Purchase line update price'

    dollar_factor = fields.Float(
        string='Dollar factor',
        default=1,
        required=True,
    )
    carrier_factor = fields.Float(
        string='Carrier factor',
        default=1,
        required=True,
    )
    extra_factor = fields.Float(
        string='Extra factor',
        default=1,
        required=True,
    )

    @api.constrains('dollar_factor', 'carrier_factor', 'extra_factor')
    def check_factor_zero(self):
        for wizard in self:
            is_factor_zero = (
                wizard.dollar_factor <= 0 or wizard.carrier_factor <= 0
                or wizard.extra_factor <= 0)
            if is_factor_zero:
                raise ValidationError(_(
                    'Factor values must be greater than 0.'))

    def update_prices(self):
        po_obj = self.env['purchase.order']
        purchase_ids = self.env.context.get('active_ids', False)
        for wizard in self:
            purchases = po_obj.browse(purchase_ids)
            for purchase in purchases:
                if purchase.state != 'draft':
                    raise UserError(_(
                        'The order must be in \'draft\' state to be '
                        'modified.'))
                for line in purchase.order_line:
                    line.price_unit = (
                        line.price_unit / wizard.dollar_factor
                        * wizard.carrier_factor * wizard.extra_factor)
        return {
            'type': 'ir.actions.act_window_close',
        }
