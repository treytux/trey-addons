###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_typology_id = fields.Many2one(
        comodel_name='res.partner.category',
        string='Partner Typology',
        domain=[('is_partner_typology', '=', True)],
        help='Partner typology used to calculate planned hours targets.',
    )
    partner_typology_min_planned_rate = fields.Float(
        string='Minimum Planned Rate',
        related='partner_typology_id.min_planned_rate',
        readonly=True,
    )
    partner_typology_max_planned_rate = fields.Float(
        string='Maximum Planned Rate',
        related='partner_typology_id.max_planned_rate',
        readonly=True,
    )
