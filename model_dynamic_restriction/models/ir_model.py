###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class IrModel(models.Model):
    _inherit = 'ir.model'

    is_restriction_create = fields.Boolean(
        string='Subscribe create',
    )
    is_restriction_write = fields.Boolean(
        string='Subscribe write',
    )
    is_restriction_unlink = fields.Boolean(
        string='Subscribe unlink',
    )
