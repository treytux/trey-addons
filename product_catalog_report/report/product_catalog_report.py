###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import UserError


class product_catalog_report(models.AbstractModel):
    _name = 'report.product_catalog_report.report_product_catalog'
    _description = 'Product Catalog Report'

    @api.model
    def get_prices_list(self, product_tmpls, pricelist):
        prices_list = {}
        for product_tmpl in product_tmpls:
            prices_list[product_tmpl.id] = pricelist.price_get(
                product_tmpl.product_variant_ids[0].id, pricelist.id)
        return prices_list

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            raise UserError(
                _('You can not launch this report from here!'))
        report = self.env['ir.actions.report']._get_report_from_name(
            'product_catalog_report.report_product_catalog')
        if 'active_ids' not in data:
            raise UserError(_('You should select at least one item!'))
        product_tmpls = self.env['product.template'].browse(data['active_ids'])
        if 'pricelist_id' not in data:
            raise UserError(_('You should select a pricelist!'))
        pricelist = self.env['product.pricelist'].browse(data['pricelist_id'])
        return {
            'data': data,
            'docs': product_tmpls,
            'doc_model': report.model,
            'prices_list': self.get_prices_list(product_tmpls, pricelist),
        }
