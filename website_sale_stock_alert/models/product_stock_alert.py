# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import api, fields, models


class ProductStockAlert(models.Model):
    _name = 'product.stock.alert'

    partner_id = fields.Many2one(
        required=True,
        comodel_name='res.partner',
        string='Partner')
    product_id = fields.Many2one(
        required=True,
        comodel_name='product.product',
        string='Product')
    notified = fields.Boolean(
        string='Notified')

    @api.one
    def notify_stock_alerts(self, template):
        self.notified = True
        template.sudo().with_context(
            lang=self.partner_id.lang).send_mail(self.id)

    @api.model
    def check_stock_alerts(self):
        alerts = self.with_context(cron=True).search([
            ('product_id.qty_available', '>', 0),
            ('notified', '=', False)])
        template = self.env.ref(
            'website_sale_stock_alert.product_stock_alert_notify_email')
        alerts.notify_stock_alerts(template)
