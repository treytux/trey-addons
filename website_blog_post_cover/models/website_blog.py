###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
import re
from odoo import models, fields, api


class BlogPost(models.Model):
    _inherit = 'blog.post'

    cover_background_image = fields.Char(
        compute='_compute_cover_background_image')

    @api.one
    def _compute_cover_background_image(self):
        bg_image = json.loads(self.cover_properties).get(
            'background-image', 'none')
        matches = re.findall(r'\((.*?)\)', bg_image)
        self.cover_background_image = matches and matches[0] or bg_image
