###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class EventProduct(models.Model):
    _name = 'event.product'
    _description = 'Produts for events'

    event_id = fields.Many2one(
        comodel_name='event.event',
        string='Event',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    name = fields.Char(
        string='Description',
    )
    quantity = fields.Float(
        string='Quantity',
        default=1,
    )
    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
    )

    @api.onchange('product_id')
    def onchange_product_id(self):
        for line in self:
            if not line.product_id:
                continue
            line.name = line.product_id.name
