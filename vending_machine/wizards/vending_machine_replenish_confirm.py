###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class VendingMachineReplenishConfirm(models.TransientModel):
    _name = 'vending.machine.replenish.confirm'
    _description = 'Vending Machine Replenish Confirm'

    vending_machine_id = fields.Many2one(
        comodel_name='vending.machine',
        string='Vending Machine',
        required=True,
        help='Reference to the vending machine',
    )

    def action_confirm(self):
        self.ensure_one()
        return self.vending_machine_id.replenish_vending_machine()
