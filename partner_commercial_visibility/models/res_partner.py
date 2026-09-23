###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.has_group(
                'partner_commercial_visibility.group_all_partners'):
            return super().create(vals_list)
        if not isinstance(vals_list, list):
            vals_list['user_id'] = self.env.user.id
        else:
            vals_list[0]['user_id'] = self.env.user.id
        return super().create(vals_list)
