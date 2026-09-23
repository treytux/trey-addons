###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        if self.env.context.get('bypass_sale_confirm_message'):
            return super().action_confirm()
        to_review = self.filtered(
            lambda o: o.state in ('draft', 'sent')
            and o.company_id.sale_confirm_message_active)
        if not to_review:
            return super().action_confirm()
        if len(to_review) > 1:
            raise UserError(_(
                'Confirm quotations one by one so their data can be reviewed '
                'against the customer-signed document.'))
        to_review.ensure_one()
        return {
            'name': _('Confirm quotation'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.confirm.message',
            'view_mode': 'form',
            'target': 'new',
            'context': dict(
                self.env.context, default_order_id=to_review.id),
        }
