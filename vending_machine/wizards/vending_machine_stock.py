###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class VendingMachineStock(models.TransientModel):
    _name = 'vending.machine.stock'
    _description = 'Vending Machine Stock Synchronization'

    vending_machine_id = fields.Many2one(
        comodel_name='vending.machine',
        string='Vending Machine',
        required=True,
        help='Reference to the vending machine',
    )
    product_line_ids = fields.One2many(
        comodel_name='vending.machine.line',
        inverse_name='wizard_id',
        string='Products',
        help='Products available in the vending machine',
    )


class VendingMachineLine(models.TransientModel):
    _name = 'vending.machine.line'
    _description = 'Vending Machine Product Line'

    wizard_id = fields.Many2one(
        comodel_name='vending.machine.stock',
        string='Vending Machine',
        required=True,
        ondelete='cascade',
        help='Reference to the vending machine',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        help='Product available in the vending machine',
    )
    product_code = fields.Char(
        string='Product Code',
        required=True,
        help='Unique code for the product in the vending machine',
    )
    selection_number = fields.Char(
        required=True,
        help='Unique code for the product in the vending machine',
    )
    stock_target = fields.Integer(
        string='Stock Target',
        required=True,
        help='Target stock level for the product in the vending machine',
    )
    stock_real = fields.Integer(
        string='Real Stock',
        required=True,
        help='Current stock level for the product in the vending machine',
    )
