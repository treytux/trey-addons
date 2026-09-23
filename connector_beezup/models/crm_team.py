###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    @api.model
    def _default_beezup_picking_policy(self):
        return self.env.user.company_id.beezup_default_picking_policy

    @api.model
    def _default_beezup_default_carrier_id(self):
        return self.env.user.company_id.beezup_carrier_id

    beezup_prefix_sale_name = fields.Char(
        string='Beezup prefix',
        help='This code is a prefix for sale order number when is imported.',
    )
    beezup_picking_policy = fields.Selection(
        string='Beezup picking policy',
        help='If automatic is selected, Beezup stock pickings will be processed'
             ' automatically.',
        selection=[
            ('auto', 'Automatic'),
            ('manual', 'Manual'),
        ],
        default=_default_beezup_picking_policy,
    )
    beezup_default_carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Default Beezup carrier',
        default=_default_beezup_default_carrier_id,
        required=True,
    )
    beezup_add_delivery_cost = fields.Boolean(
        string='Add delivery costs',
    )
    beezup_auto_cancel_orders = fields.Boolean(
        string='Auto cancel Beezup orders',
        default=True,
    )
    avoid_beezup_sync = fields.Boolean(
        string='Prevent sync with Beezup',
    )
    beezup_sync_date_start = fields.Datetime(
        string='Beezup sync date start',
    )
