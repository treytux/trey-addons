###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ContractLine(models.Model):
    _inherit = 'contract.line'

    lot_ids = fields.Many2many(
        comodel_name='stock.lot',
        relation='contract_line2stock_production_lot_rel',
        column1='contract_line_id',
        column2='lot_id',
        string='Lots',
    )
