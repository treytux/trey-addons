# Copyright 2019 Vicent Cubells - Trey <http://www.trey.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    multiple_discount = fields.Char(
        string='Disc. (%)',
    )

    @api.onchange('name')
    def onchange_name(self):
        """Apply the default supplier discounts of the selected supplier"""
        for supplierinfo in self.filtered('name'):
            supplierinfo.multiple_discount = \
                supplierinfo.name.default_supplierinfo_multiple_discount
        return super().onchange_name()

    @api.model
    def _get_po_to_supplierinfo_synced_fields(self):
        res = super()._get_po_to_supplierinfo_synced_fields()
        res += ['multiple_discount']
        return res
