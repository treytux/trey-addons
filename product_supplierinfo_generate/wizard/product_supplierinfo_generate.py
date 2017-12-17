# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _


class GenerateProductSupplierInfo(models.TransientModel):
    _name = 'wiz.generate_product_supplierinfo'
    _description = 'Generate product supplierinfo'
    name = fields.Char(
        string='Name')
    count = fields.Integer(
        string='Count',
        readonly=True)

    @api.multi
    def action_accept(self):
        self.count = 0
        for supplier in self.env['product.supplierinfo'].search([
                ('pricelist_ids', '=', False)]):
            self.env['pricelist.partnerinfo'].create({
                'min_quantity': 1.0,
                'price': 0.0,
                'suppinfo_id': supplier.id})
            self.count += 1
        res = self.env['ir.model.data'].get_object_reference(
            'generate_product_supplierinfo',
            'view_count_generate_product_supplierinfo')
        res_id = res and res[1] or False
        return {
            'name': _('Generate product supplierinfo'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'wiz.generate_product_supplierinfo',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new'}
