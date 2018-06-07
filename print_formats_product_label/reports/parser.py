# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, exceptions, _, api
from functools import partial
from reportlab.graphics.barcode import createBarcodeDrawing


class ProductLabelReport(models.AbstractModel):
    _name = 'report.print_formats_product_label.label'

    @api.model
    def format_currency(self, value):
        return str('%.2f' % value).replace('.', ',')

    @api.model
    def get_price(self, product):
        pricelists = self.env['product.pricelist'].search([
            ('name', 'ilike', 'Public Pricelist'), ('type', '=', 'sale')])
        if not pricelists.exists():
            pricelists = self.env['product.pricelist'].search([
                ('type', '=', 'sale')], order='id')
        if pricelists:
            prices = pricelists[0].price_get(product.id, 1)
            price_unit = prices[pricelists[0].id]
            price = product.taxes_id.compute_all(price_unit, 1)
            return price['total_included']
        else:
            return 0.00

    @api.model
    def print_barcode(self, value, width, height):
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
    def format_size(self, value, size):
        try:
            return value[:size]
        except:
            return value

    @api.model
    def get_variant_name(self, product):
        return '%s %s' % (
            product.name,
            '-'.join([v.name for v in product.attribute_value_ids]))

    @api.multi
    def render_product_label(self, docargs, data):
        docargs.update({
            'docs': self,
            'tmpl_name': 'print_formats_product_label.label_document'})
        return docargs

    @api.multi
    def render_html(self, data=None):
        docargs = {
            'doc_ids': self.ids,
            'doc_model': 'product.product',
            'format_currency': partial(self.format_currency),
            'get_price': partial(self.get_price),
            'print_barcode': partial(self.print_barcode),
            'format_size': partial(self.format_size),
            'get_variant_name': partial(self.get_variant_name)}
        render_func = self.env.context.get(
            'render_func', 'render_product_label')
        if hasattr(self, render_func):
            fnc = getattr(self, render_func)
            fnc(docargs, data)
        else:
            raise exceptions.Warning(_(
                'Don\'t have render func %s in object') % render_func)
        if not self.ids:
            raise exceptions.Warning(_('You must choose at least one record.'))
        return self.env['report'].browse(self.ids[0]).with_context(
            self.env.context).render(
            'print_formats_product_label.label', docargs)
