###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    custom_date_planned = fields.Datetime(
        string='Custom Date Planned',
        readonly=True,
        states={
            'draft': [('readonly', False)],
            'sent': [('readonly', False)],
            'to approve': [('readonly', False)],
        },
        help='Force delivery expected date before quotation were confirmed.',
    )

    @api.multi
    def button_confirm(self):
        res = super().button_confirm()
        for order in self:
            if not order.picking_ids or not order.custom_date_planned:
                continue
            for picking in order.picking_ids:
                picking.scheduled_date = order.custom_date_planned
                if picking.move_lines:
                    picking.move_lines.write({
                        'scheduled_date': order.custom_date_planned,
                    })
        return res
