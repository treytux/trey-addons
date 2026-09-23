###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class InstoreErrorMapping(models.Model):
    _name = 'instore.error.mapping'
    _description = 'InStore error mapping'

    code = fields.Integer(
        string='Error Code',
        required=True,
    )
    description = fields.Text(
        string='Description',
        required=True,
        translate=True,
    )
