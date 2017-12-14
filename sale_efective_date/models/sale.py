# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api
from datetime import timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _default_validity_date(self):
        validity_date_str = False
        company_pool = self.env['res.company']
        company_id = company_pool._company_default_get('sale.order')
        company = company_pool.browse(company_id)
        if company.default_sale_order_validity_days:
            today_str = fields.Date.context_today(self)
            today = fields.Date.from_string(today_str)
            validity_date = today + timedelta(
                days=company.default_sale_order_validity_days or 0)
            validity_date_str = fields.Date.to_string(validity_date)
        return validity_date_str

    validity_date = fields.Date(
        string="Validity Date",
        required=True,
        default=_default_validity_date)

    @api.onchange('date_order')
    def _onchange_date_order(self):
        if self.date_order:
            company = self.company_id or self.env.user.company_id
            if not company.default_sale_order_validity_days:
                return
            dorder = fields.Datetime.from_string(self.date_order).date()
            validity_date = dorder + timedelta(
                days=company.default_sale_order_validity_days)
            self.validity_date = fields.Date.to_string(validity_date)
