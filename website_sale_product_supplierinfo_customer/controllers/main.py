###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    @http.route()
    def payment(self, **post):
        res = super().payment(**post)
        order = request.website.sale_get_order()
        if not order:
            return res
        partner = order.partner_id.commercial_partner_id
        for order_line in order.order_line:
            product_tmpl = order_line.product_id.product_tmpl_id
            qty = order_line.product_uom_qty
            customerinfo = product_tmpl.get_product_customerinfo(
                product_tmpl.id, qty, partner, order_line.product_id.id)
            if customerinfo.price or customerinfo.discount:
                order_line.discount = customerinfo.discount
                order_line.price_unit = customerinfo.price
        return res

    def combination_info_compute_price_with_taxes(
            self, res, partner, supplierinfo, add_qty):
        current_website = request.env['website'].get_current_website()
        company_id = current_website.company_id
        product = request.env['product.product'].browse(res['product_id'])
        has_group = request.env.user.has_group(
            'account.group_show_line_subtotals_tax_excluded')
        tax_display = has_group and 'total_excluded' or 'total_included'
        account_fiscal_position_obj = request.env['account.fiscal.position']
        fiscal_position = account_fiscal_position_obj.sudo().with_context(
            force_company=company_id.id).get_fiscal_position(partner.id)
        taxes = account_fiscal_position_obj.browse(fiscal_position).map_tax(
            product.sudo().taxes_id.filtered(
                lambda x: x.company_id == company_id), product, partner)
        price = request.env['account.tax']._fix_tax_included_price_company(
            supplierinfo.price, product.sudo().taxes_id, taxes, company_id)
        pricelist = current_website.get_current_website()
        price = taxes.compute_all(
            price, pricelist.currency_id, add_qty, product,
            partner)[tax_display]
        return price

    @http.route()
    def get_combination_info_website(
            self, product_template_id, product_id, combination, add_qty, **kw):
        res = super().get_combination_info_website(
            product_template_id, product_id, combination, add_qty, **kw)
        quantity = request.env.context.get('quantity', add_qty)
        partner_id = request.env.user.partner_id.commercial_partner_id
        supplierinfo = (
            request.env['product.template'].get_product_customerinfo(
                product_template_id, quantity, partner_id, res['product_id']))
        if supplierinfo.price:
            price = self.combination_info_compute_price_with_taxes(
                res, partner_id, supplierinfo, add_qty)
            res['price'] = price
        return res
