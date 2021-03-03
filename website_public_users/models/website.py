###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class Website(models.Model):
    _inherit = "website"

    def _get_default_website_public_users_domain(self):
        return [('groups_id', 'in', self.env.ref('base.group_public').id)]

    website_public_users = fields.Many2many(
        comodel_name='res.users',
        domain=lambda self: self._get_default_website_public_users_domain(),
        string='Website Public Users',
    )

    @api.multi
    def sale_get_order(self, force_create=False, code=None,
                       update_pricelist=False, force_pricelist=False):
        self.ensure_one()
        if self.env.user.id in self.website_public_users.ids:
            self.env.user.partner_id.last_website_so_id = False
        return super().sale_get_order(
            force_create, code, update_pricelist, force_pricelist)
