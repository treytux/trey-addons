###############################################################################
# For copyright and license notices, see __manifest__.py file
###############################################################################
from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    sale_order_type_id = fields.Many2one(
        comodel_name='sale.order.type',
        string='Sale Order Type',
    )
