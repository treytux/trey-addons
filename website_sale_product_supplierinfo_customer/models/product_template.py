###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_combination_info(
            self, combination=False, product_id=False, add_qty=1,
            pricelist=False, parent_combination=False, only_template=False):
        combination_info = super()._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty,
            pricelist=pricelist, parent_combination=parent_combination,
            only_template=only_template)
        if not self.env.context.get('website_id') or not pricelist:
            return combination_info
        product = self.env['product.product'].browse(
            combination_info['product_id']) or self
        partner = self.env.user.partner_id.commercial_partner_id
        customerinfo = self.get_product_customerinfo(
            self.id, add_qty, partner, product.id)
        if not customerinfo:
            return combination_info
        website = self.env['website'].get_current_website()
        company = website.company_id
        customer_price = customerinfo.currency_id._convert(
            customerinfo.price, pricelist.currency_id, company,
            fields.Date.context_today(self), round=False)
        price = customer_price * (1 - customerinfo.discount / 100.0)
        product_taxes = product.sudo().taxes_id.filtered(
            lambda tax: tax.company_id == company)
        fiscal_position_id = self.env['website'].sudo().\
            _get_current_fiscal_position_id(partner)
        fiscal_position = self.env['account.fiscal.position'].sudo().browse(
            fiscal_position_id)
        taxes = fiscal_position.map_tax(product_taxes)
        tax_price_args = (
            product_taxes, taxes, company.id, pricelist, product, partner)
        price = self._price_with_tax_computed(price, *tax_price_args)
        list_price = combination_info['list_price']
        if customerinfo.discount:
            list_price = self._price_with_tax_computed(
                customer_price, *tax_price_args)
        combination_info.update(
            price=price, list_price=list_price,
            has_discounted_price=pricelist.currency_id.compare_amounts(
                list_price, price) == 1)
        return combination_info

    def get_product_customerinfo(
            self, product_template_id, quantity, partner_id, product_id=False):
        date_today = fields.date.today()
        customerinfos = self.env['product.customerinfo'].sudo().search([
            '|',
            ('partner_id', '=', partner_id.id),
            ('partner_id', '=', False),
            ('min_qty', '<=', quantity),
            '|',
            ('product_id', '=', product_id),
            '&',
            ('product_tmpl_id', '=', product_template_id),
            ('product_id', '=', False),
        ], order='product_id desc, sequence, min_qty desc, price')
        customerinfo = self.env['product.customerinfo']
        for custom_info in customerinfos:
            if custom_info.date_start and custom_info.date_start > date_today:
                continue
            if custom_info.date_end and custom_info.date_end < date_today:
                continue
            customerinfo = custom_info
            break
        return customerinfo
