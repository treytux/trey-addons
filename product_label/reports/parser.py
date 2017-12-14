# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, exceptions, _, api
from functools import partial
from reportlab.graphics.barcode import createBarcodeDrawing


class ProductLabelReport(models.AbstractModel):
    _name = 'report.product_label.label'

    @api.multi
    def render_product_label(self, docargs, data):
        docargs.update({
            'docs': self,
            'tmpl_name': 'product_label.label_document',
        })
        return docargs

    @api.multi
    def render_html(self, data=None):
        docargs = {
            'doc_ids': self.ids,
            'doc_model': 'product.product',
            'formatCurrency': self.formatCurrency,
            'getPrice': partial(self.getPrice),
            'printBarcode': partial(self.printBarcode),
            'formatSize': partial(self.formatSize),
        }

        render_func = self.env.context.get(
            'render_func',
            'render_product_label')
        if hasattr(self, render_func):
            fnc = getattr(self, render_func)
            fnc(docargs, data)
        else:
            raise exceptions.Warning(
                _('Don\'t have render func %s in object' % render_func))

        report = self.env['report'].browse(self.ids[0])
        return report.with_context(
            self.env.context).render('product_label.label', docargs)

    @api.model
    def formatCurrency(self, value):
        return str('%.2f' % value).replace('.', ',')

    @api.model
    def getPrice(self, product):
        pricelists = self.env['product.pricelist'].search([
            ('name', 'ilike', 'Public Pricelist'), ('type', '=', 'sale')])

        if not pricelists.exists():
            pricelists = self.env['product.pricelist'].search([
                ('type', '=', 'sale')])

        if pricelists:
            prices = pricelists[0].price_get(product.id, 1)
            price_unit = prices[pricelists[0].id]
            price = product.taxes_id.compute_all(price_unit, 1)
            return price['total_included']
        else:
            return 0.00

    @api.model
    def printBarcode(self, value, width, height):
        try:
            width, height = int(width), int(height)
            barcode = createBarcodeDrawing(
                'EAN13', value=value, format='png', width=width, height=height)
            barcode = barcode.asString('png')
            barcode = barcode.encode('base64', 'strict')
        except (ValueError, AttributeError):
            raise exceptions.Warning(_('Cannot convert into barcode.'))
        return barcode

    @api.model
    def formatSize(self, value, size):
        try:
            return value[:size]
        except:
            return value
