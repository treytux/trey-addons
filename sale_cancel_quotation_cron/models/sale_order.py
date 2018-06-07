# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api
from datetime import timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def cron_cancel_old_quotations(self):
        today_str = fields.Date.context_today(self)
        today = fields.Date.from_string(today_str)
        companies = self.env['res.company'].search([
            ('days_to_cancel', '>', 0)])
        for company in companies:
            date2cancel = today - timedelta(days=company.days_to_cancel)
            date2cancel_str = fields.Date.to_string(date2cancel)
            sale_quotations = self.env['sale.order'].search([
                ('state', '=', 'draft'),
                ('date_order', '<=', date2cancel_str)])
            for sale_quotation in sale_quotations:
                sale_quotation.action_cancel()
