###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class BlogPost(models.Model):
    _name = 'blog.post'
    _inherit = ['blog.post', 'ir.translatable.mixin']
