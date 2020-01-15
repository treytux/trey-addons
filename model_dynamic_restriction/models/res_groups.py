###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResGroups(models.Model):
    _inherit = 'res.groups'

    restriction_ids = fields.Many2many(
        comodel_name='ir.model.restriction',
        relation='ir_model_restriction2res_groups_rel',
        column1='group_ids',
        column2='restriction_id',
    )
