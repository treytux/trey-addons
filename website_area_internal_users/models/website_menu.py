###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models
from odoo.http import request


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    internal_only = fields.Boolean(
        string='Visible for internal users only',
        help='If checked, the menu will be displayed when the logged user '
             'were internal type and give access.'
    )

    def _compute_visible(self):
        super()._compute_visible()
        for website_menu in self:
            if not website_menu.is_visible:
                return
            if website_menu.internal_only:
                website_menu.is_visible = request.env.user.has_group(
                    'base.group_user')
