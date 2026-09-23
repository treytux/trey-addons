###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    portal_access_scope = fields.Selection(
        selection=[
            ('portal', 'Block portal users'),
            ('employee', 'Block employee users'),
            ('both', 'Block portal and employee users'),
        ],
        string='Portal access',
    )

    def get_portal_access_scope(self):
        return self.portal_access_scope

    def get_portal_access(self, user):
        if (
            user._is_internal()
                and self.portal_access_scope in ['both', 'employee']):
            return False
        if (
            user.has_group('base.group_portal')
                and self.portal_access_scope in ['both', 'portal']):
            return False
        return True
