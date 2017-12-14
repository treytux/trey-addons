# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class WizProductBarcodeGeneratorList(models.TransientModel):
    _name = 'wiz.product.barcode.generator.list'
    _description = 'Generate EAN13 from product tree.'

    name = fields.Char(
        string='Name')

    @api.multi
    def button_accept(self):
        products = self.env['product.product'].browse(
            self.env.context.get('active_ids', []))
        for product in products:
            product.generate_ean13()
        return {'type': 'ir.actions.act_window_close'}
