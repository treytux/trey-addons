###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api


class BlogPost(models.Model):
    _inherit = 'blog.post'

    is_public = fields.Boolean(
        string='Is Public',
        help='Allow or deny post access for public users',
        default=True)

    @api.multi
    def toggle_public(self):
        for record in self:
            record.is_public = not record.is_public
