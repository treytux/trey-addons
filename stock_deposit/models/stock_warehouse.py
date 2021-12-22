###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    deposit_parent_id = fields.Many2one(
        comodel_name='stock.location',
        string='Deposit parent',
        domain='[("usage", "=", "view")]',
        required=True,
        help='This location must be view type.',
    )

    @api.constrains('deposit_parent_id')
    def _check_usage_deposit_parent_id(self):
        if self.deposit_parent_id and self.deposit_parent_id.usage != 'view':
            raise UserError(_(
                'Deposit parent must be a location of \'view\' type!'))
