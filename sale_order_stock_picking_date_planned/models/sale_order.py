###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    date_planned = fields.Datetime(
        string='Custom Date Planned',
        readonly=True,
        states={
            'draft': [('readonly', False)],
            'sent': [('readonly', False)],
        },
        help='Force delivery expected date before quotation were confirmed.',
    )

    @api.multi
    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            if not order.picking_ids or not order.date_planned:
                continue
            for picking in order.picking_ids:
                picking.scheduled_date = order.date_planned
                if picking.move_lines:
                    picking.move_lines.write({
                        'scheduled_date': order.date_planned
                    })
        return res
