###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockNumberPackageValidateWizard(models.TransientModel):
    _inherit = 'stock.number.package.validate.wizard'

    def _compute_print_package_label(self):
        res = super()._compute_print_package_label()
        for wizard in self:
            if 'tipsa' in wizard.pick_ids.mapped('delivery_type'):
                wizard.print_package_label = False
        return res
