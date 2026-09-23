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
        string='Zones',
    )

    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        if 'zone_ids' in vals:
            self.env['ir.model.access'].call_cache_clearing_methods()
            self.env['ir.rule'].clear_caches()
        return res
