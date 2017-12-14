# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _get_supplier_invoice_count(self):
        for partner in self:
            partner.supplier_inv_and_ref_count = self.env[
                'account.invoice'].search_count([
                    ('partner_id', 'child_of', partner.id),
                    ('type', 'in', ('in_invoice', 'in_refund'))])

    supplier_inv_and_ref_count = fields.Integer(
        string='Supplier Inv.',
        compute=_get_supplier_invoice_count)
