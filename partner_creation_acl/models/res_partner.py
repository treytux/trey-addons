###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, values):
        if not self.env.user.has_group(
                'partner_creation_acl.group_partner_creation'):
            raise ValidationError(_('You are not allowed to create partners.'))
        return super().create(values)
