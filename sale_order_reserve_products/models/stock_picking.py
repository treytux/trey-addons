###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import _, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    customer_reservation = fields.Boolean(
        string='Customer reservation',
        copy=False,
    )
    sale_reservation = fields.Many2one(
        comodel_name='sale.order',
        string='Sale for reservation',
        copy=False,
    )

    def get_unreserve_picking_domain(self):
        return [
            ('customer_reservation', '=', True),
            ('state', '=', 'assigned'),
        ]

    def cron_unreserve_sale_pickings(self):
        days = self.env['ir.config_parameter'].sudo().get_param(
            'sale_order_reserve_products.days_to_unreserve_pickings')
        today = fields.Datetime.today()
        pickings = self.env['stock.picking'].search(
            self.get_unreserve_picking_domain())
        for picking in pickings:
            if picking.create_date + timedelta(days=int(days)) <= today:
                continue
            picking.do_unreserve()
            picking.action_cancel()
            msg = _('Reservation canceled with planned action for exceeding '
                    'the days without confirmation')
            picking.message_post(body=msg)
            picking.sale_reservation.customer_reservation = False
