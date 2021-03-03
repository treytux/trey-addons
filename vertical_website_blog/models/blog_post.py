###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class BlogPost(models.Model):
    _inherit = 'blog.post'
    _order = 'post_date DESC, id DESC'
