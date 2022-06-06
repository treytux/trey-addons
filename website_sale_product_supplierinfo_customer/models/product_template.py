###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def get_product_customerinfo(
            self, product_template_id, quantity, partner_id, product_id=False):
        date_today = fields.date.today()
        customerinfos = self.env['product.customerinfo'].sudo().search([
            '|',
            ('name', '=', partner_id.id),
            ('name', '=', None),
            ('min_qty', '<=', quantity),
            '|',
            ('product_id', '=', product_id),
            '&',
            ('product_tmpl_id', '=', product_template_id),
            ('product_id', '=', False),
        ], order='product_id, sequence, min_qty desc, price')
        customerinfo = self.env['product.customerinfo']
        for custom_info in customerinfos:
            if custom_info.date_start and custom_info.date_start > date_today:
                continue
            if custom_info.date_end and custom_info.date_end < date_today:
                continue
            customerinfo = custom_info
            break
        return customerinfo
