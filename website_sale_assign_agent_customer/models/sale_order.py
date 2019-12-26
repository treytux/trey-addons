###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    agent_customer = fields.Many2one(
        comodel_name='res.partner',
        string='Agent Customer')
