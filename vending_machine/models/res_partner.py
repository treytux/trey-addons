###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    unified_so_for_vending_machines = fields.Boolean(
        string='Unified Sale Order for Vending Machines',
        help='If checked, all sales from vending machines for this partner will'
        ' be grouped into a single sale order.',
        default=False,
    )
    machine_ids = fields.One2many(
        'vending.machine',
        'parent_id',
        string='Vending Machines',
        help='The vending machines associated with this partner.',
        readonly=True,
    )
