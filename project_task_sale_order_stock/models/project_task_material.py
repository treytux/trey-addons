##############################################################################
# For copyright and license notices, see __manifest__.py file in root
# directory
##############################################################################
from odoo import fields, models


class ProjectTaskMaterial(models.Model):
    _inherit = 'project.task.material'

    sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale order line',
        copy=False,
        ondelete='restrict',
    )
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lot/Serial number',
        domain='[("product_id", "=", product_id)]',
    )
