###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_simulator = fields.Boolean(
        string='Access Simulator',
        compute='compute_is_simulator',
        store=True,
    )
    ede_workflow_state = fields.Selection(
        string='EDE / Workflow State',
        old_name='adarra_ede_state',
        selection=[
            ('draft', 'Draft'),
            ('simulated', 'Simulated'),
            ('send', 'Send'),
            ('purchase', 'Purchase Received'),
            ('sale', 'Sale Received'),
            ('email', 'Email Pending'),
            ('done', 'Done'),
        ],
        default='draft',
        copy=False,
        track_visibility='onchange',
    )

    @api.depends('order_line.product_id')
    def compute_is_simulator(self):
        for order in self:
            lines = order.order_line.filtered(lambda l: l.is_simulator)
            order.is_simulator = bool(lines)
