###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, models


class PurchaseOrderJoin(models.TransientModel):
    _name = 'purchase.order.join'
    _description = 'Wizard for join purchase quotations'

    def action_join(self):
        assert self._context.get('active_ids'), 'Missing active_ids'
        orders = self.env['purchase.order'].browse(self._context['active_ids'])
        if len(orders) <= 1 :
            raise exceptions.UserError(
                _('Select more than one quotation in draft state'))
        orders = orders.filtered(lambda o: o.state == 'draft')
        if len(orders) <= 1 :
            raise exceptions.UserError(_('Select quotations in draft state'))
        partner = orders[0].partner_id
        partner_orders = orders.filtered(lambda o: o.partner_id == partner)
        if len(orders) != len(partner_orders):
            raise exceptions.UserError(
                _('You can only join quotes from the same supplier'))
        base_order = orders[0]
        base_order.origin = ','.join([o for o in orders.mapped('origin') if o])
        for order in orders:
            if order == base_order:
                continue
            order.order_line.write({'order_id': base_order.id})
            order.state = 'cancel'
            order.unlink()
        action = self.env.ref('purchase.purchase_rfq')
        res = action.read()[0]
        res.update({
            'res_id': base_order.id,
            'view_type': 'form',
            'view_mode': 'form',
        })
        return res
