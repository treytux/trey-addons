# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields


class PurchaseConfigSettings(models.TransientModel):
    _inherit = 'purchase.config.settings'

    inv_number_unique = fields.Boolean(
        string='Supplier invoice number unique',
        help='Block invoice validating when supplier number already exists',
    )
    inv_ref_unique = fields.Boolean(
        string='Payment reference unique',
        help='Block invoice validating when reference already exists',
    )

    def _get_params(self):
        return [
            ('inv_number_unique',
             'account_invoice_supplier_unique.inv_number_unique'),
            ('inv_ref_unique',
             'account_invoice_supplier_unique.inv_reference_uniq'),
        ]

    @api.multi
    def set_params(self):
        self.ensure_one()
        for field_name, key_name in self._get_params():
            value = str(getattr(self, field_name))
            self.env['ir.config_parameter'].set_param(key_name, value)

    @api.model
    def default_get(self, fields):
        res = super(PurchaseConfigSettings, self).default_get(fields)
        for field_name, key_name in self._get_params():
            val = self.env['ir.config_parameter'].get_param(key_name, False)
            res[field_name] = (val == 'True' and True or False)
        return res
