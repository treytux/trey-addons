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
    product_type = fields.Selection(
        related='product_id.type',
    )
    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task',
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible',
    )
    address_id = fields.Many2one(
        comodel_name='res.partner',
        string='Address',
    )
    generated = fields.Boolean(
        readonly=True,
        compute='_compute_generated',
    )

    @api.onchange('product_id')
    def onchange_product_id(self):
        for line in self:
            if not line.product_id:
                continue
            line.name = line.product_id.name

    @api.depends('task_id')
    def _compute_generated(self):
        for line in self:
            line.generated = bool(line.task_id)

    def create_services_and_material_line(self):
        for line in self:
            line.event_id.create_services_and_material(
                product_ids=line.product_id.ids, product_lines=line)
