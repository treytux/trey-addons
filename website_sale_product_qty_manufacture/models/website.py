###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class Website(models.Model):
    _inherit = 'website'

    def sale_get_order(self, force_create=False, update_pricelist=False, **kwargs):
        self = self.with_context(qty_manufacture_add_to_virtual=True)
        return super(Website, self).sale_get_order(
            force_create=force_create,
            update_pricelist=update_pricelist,
            **kwargs
        )
