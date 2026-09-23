###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _add_supplier_to_product(self):
        return super(PurchaseOrder, self.with_context(
            check_auto_creation=True))._add_supplier_to_product()
