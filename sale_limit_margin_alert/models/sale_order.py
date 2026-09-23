###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        res = super().action_confirm()
        for sale in self:
            company_id = sale.company_id
            msg_list = []
            for line in sale.order_line.filtered(
                    lambda ln:
                    company_id.include_delivery_lines == ln.is_delivery):
                price_dto = line.price_unit - (
                    line.price_unit * (line.discount / 100))
                cost = line.purchase_price or line.product_id.standard_price
                margin = cost / (price_dto or 0.01)
                margin = round((margin - 1) * -100, 2)
                if margin < company_id.margin_limit:
                    msg = 'Line with product [%s] has a limit lower than ' \
                          'that established in the company. ' \
                          'Unit price: [%s] - Cost: [%s] - Discount: [%s] -' \
                          ' Margin: [%s] - Margin limit: [%s]'
                    msg = msg % (
                        line.product_id.default_code, line.price_unit,
                        line.purchase_price, line.discount,
                        line.margin, company_id.margin_limit)
                    msg_list.append(msg)
            if len(msg_list) > 0:
                if company_id.notification_method == 'team_manager':
                    if not line.order_id.team_id or (
                            not line.order_id.team_id.user_id):
                        user_id = company_id.notification_user
                    else:
                        user_id = line.order_id.team_id.user_id
                elif company_id.notification_method == 'user_unique':
                    user_id = company_id.notification_user
                res_model_id = self.env['ir.model']._get('sale.order').id
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref(
                        'mail.mail_activity_data_warning').id,
                    'res_id': line.order_id.id,
                    'res_model_id': res_model_id,
                    'user_id': user_id.id,
                    'date_deadline': (
                        fields.Date.today() + timedelta(days=7)),
                    'note': '<br/>'.join(msg_list),
                    'summary': _('Margin limit alert on sales order'),
                })
        return res
