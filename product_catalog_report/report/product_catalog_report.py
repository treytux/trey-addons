###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models
from odoo.exceptions import ValidationError
from bs4 import BeautifulSoup


class product_catalog_report(models.AbstractModel):
    _name = 'report.product_catalog_report.report_product_catalog'

    @api.model
    def get_text(self, html_text, length=0):
        text = BeautifulSoup(html_text, 'lxml').get_text()
        return length == 0 and text or text[:length]

    @api.model
    def get_price(self, product, pricelist):
        price = pricelist.price_get(product.id, 1)
        return price and list(price.values())[0] or 0

    @api.model
    def get_report_values(self, doc_ids, data=None):
        if not data:
            raise ValidationError('You can not launch this report from here!')
        doc_ids = data['active_ids']
        report = self.env['ir.actions.report']._get_report_from_name(
            'product_catalog_report.report_product_catalog')
        product_tmpls = self.env['product.template'].browse(doc_ids)
        return {
            'doc_ids': doc_ids,
            'doc_model': report.model,
            'docs': product_tmpls,
            'data': data,
            'get_text': self.get_text,
            'get_price': self.get_price,
            'pricelist': self.env['product.pricelist'].browse(
                int(data['pricelist_id']))}
