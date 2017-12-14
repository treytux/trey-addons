# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    generate_task = fields.Boolean(
        string="Generate Task")
    history_line_id = fields.Many2one(
        comodel_name="simulation.cost.history.line",
        string="Sumulation Line",
        required=False)
