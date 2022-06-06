###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    @api.model
    def _default_beezup_picking_policy(self):
        return self.env.user.company_id.beezup_default_picking_policy

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
