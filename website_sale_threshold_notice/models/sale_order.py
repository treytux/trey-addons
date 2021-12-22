###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _cart_update(
            self, product_id=None, line_id=None, add_qty=0, set_qty=0,
            **kwargs):
        values = super()._cart_update(
            product_id=product_id, line_id=line_id, add_qty=add_qty,
            set_qty=set_qty, **kwargs)
        for line in self.order_line:
            if line.warning_stock and self.partner_id.user_id:
                template = self.env.ref(
                    '%s.%s' % (
                        'website_sale_threshold_notice',
                        'salesman_notice_email_template'))
                template.sudo().with_context(
                    lang=self.env.user.lang).send_mail(line.id)
        return values
