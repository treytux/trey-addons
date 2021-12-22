###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    zone_ids = fields.Many2many(
        comodel_name='res.partner.zone',
        relation='res_partner_zone2res_users_rel',
        column1='user_id',
        column2='zone_id',
    )
