###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models
from odoo.http import request


class WebsitePage(models.Model):
    _inherit = 'website.page'

    internal_only = fields.Boolean(
        string='Visible for internal users only',
        help='If checked, the page will be displayed when the logged user '
             'were internal type and give access.'
    )

    def _compute_visible(self):
        super()._compute_visible()
        for website_page in self:
            if not website_page.is_visible:
                return
            if website_page.internal_only:
                website_page.is_visible = request.env.user.has_group(
                    'base.group_user')
