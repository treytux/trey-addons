###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def search_product_customerinfo(self, line):
        date_order = line.order_id.date_order.date()
        partner = line.order_id.partner_id
        customerinfos = self.env['product.customerinfo'].search(
            [
                ('name', '=', partner.id),
                ('price', '=', line.price_unit),
                ('min_qty', '<=', line.product_uom_qty),
                '|',
                ('product_id', '=', line.product_id.id),
                '&',
                ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                ('product_id', '=', False),
            ],
            order='product_id, sequence, min_qty desc, price')
        customerinfo = self.env['product.customerinfo']
        if not customerinfos:
            return customerinfo
        for custom_info in customerinfos:
            if custom_info.date_start and custom_info.date_start > date_order:
                continue
            if custom_info.date_end and custom_info.date_end < date_order:
                continue
            customerinfo = custom_info
            break
        return customerinfo

    def action_request_permission(self):
        if not self.check_order_margin_limits():
            if not self.user_id:
                raise ValidationError(
                    _('Mail cannot be sent because no salesperson is assigned')
                )
            template = self.env.ref(
                'sale_user_limit_margin.email_template_limit_margin')
            template.sudo().with_context(
                lang=self.env.user.lang).send_mail(self.id)
            msg = _(
                'An email has been sent to salesperson %s for review and '
                'confirm this sale order. Date: %s') % (
                    self.user_id, fields.Datetime.now())
            self.message_post(body=msg)

    def check_order_margin_limits(self):
        self.ensure_one()
        if not self.env.user.apply_margin_limit:
            return True
        for line in self.order_line:
            customerinfo = self.search_product_customerinfo(line)
            if customerinfo and customerinfo.price == line.price_unit and (
                    customerinfo.discount == line.discount):
                continue
            price_dto = line.price_unit - (
                line.price_unit * (line.discount / 100))
            cost = line.standard_price or line.product_id.standard_price
            margin = cost / (price_dto or 0.01)
            margin = round((margin - 1) * -100, 2)
            if margin < self.env.user.sales_margin_limit:
                return False
        return True

    def get_margin_limit_msg_error(self):
        raise ValidationError(
            _('Sales margin limits [%s] exceeded by the user %s') % (
                self.env.user.sales_margin_limit, self.env.user.name))

    @api.multi
    def action_confirm(self):
        if not self.check_order_margin_limits():
            self.get_margin_limit_msg_error()
        return super().action_confirm()

    @api.multi
    def action_done(self):
        if not self.check_order_margin_limits():
            self.get_margin_limit_msg_error()
        return super().action_done()

    @api.multi
    def action_cancel(self):
        if not self.check_order_margin_limits():
            self.get_margin_limit_msg_error()
        return super().action_cancel()

    @api.multi
    def recalculate_prices(self):
        if not self.check_order_margin_limits():
            self.get_margin_limit_msg_error()
        return super().recalculate_prices()

    @api.multi
    def recalculate_names(self):
        if not self.check_order_margin_limits():
            self.get_margin_limit_msg_error()
        return super().recalculate_names()

    @api.multi
    def action_quotation_send(self):
        if not self.check_order_margin_limits():
            self.get_margin_limit_msg_error()
        return super().action_quotation_send()

    @api.multi
    def print_quotation(self):
        if not self.check_order_margin_limits():
            self.get_margin_limit_msg_error()
        return super().print_quotation()

    @api.multi
    def preview_sale_order(self):
        if not self.check_order_margin_limits():
            self.get_margin_limit_msg_error()
        return super().preview_sale_order()
