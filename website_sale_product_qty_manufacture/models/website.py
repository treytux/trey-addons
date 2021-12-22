###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class Website(models.Model):
    _inherit = 'website'

    def sale_get_order(
        self, force_create=False, code=None, update_pricelist=False,
            force_pricelist=False):
        self = self.with_context(qty_manufacture_add_to_virtual=True)
        return super(Website, self).sale_get_order(
            force_create=force_create, code=code,
            update_pricelist=update_pricelist, force_pricelist=force_pricelist)
