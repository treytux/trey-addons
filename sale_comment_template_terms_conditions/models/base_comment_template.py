###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class BaseCommentTemplate(models.Model):
    _inherit = 'base.comment.template'

    is_condition = fields.Boolean(
        string='Is Terms & Conditions',
    )
