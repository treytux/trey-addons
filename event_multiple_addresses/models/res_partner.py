###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    extra_address_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='res_partner_extra_address_rel',
        column1='partner_id',
        column2='extra_address_id',
        string='Extra locations',
    )
