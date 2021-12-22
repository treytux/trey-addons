###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class BaseException(models.Model):
    _name = 'base.manage.exception'
    _description = 'Base manage exception'

    name = fields.Char(
        string='Name',
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name='base.manage.exception.line',
        inverse_name='exception_id',
        string='Exception lines',
    )
