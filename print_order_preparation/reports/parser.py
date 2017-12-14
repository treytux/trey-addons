# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api
from functools import partial
import math


class PrintOrderPreparation(models.TransientModel):
    _name = 'report.print_order_preparation.report_order_preparation'

    @api.multi
    def get_order_lines_by_loc(self, order):
        d = {}
        for l in order.order_line:
            loc = l.product_id and l.product_id.loc_rack or ''
            d['%s-%s' % (loc, l.id)] = l
        return d

    @api.multi
    def sort_keys(self, list_val):
        return sorted(list_val)

    @api.multi
    def get_taxes(self, order):
        taxes = {}
        for line in order.order_line:
            for tax in line.tax_id:
                t = tax.compute_all(
                    line.price_unit * (1 - (line.discount or 0.0) / 100.0),
                    line.product_uom_qty,
                    line.product_id,
                    line.order_id.partner_id
                )['taxes']
                if len(t) > 0 and t[0]['name'] not in taxes:
                    taxes[t[0]['name']] = 0
                taxes[t[0]['name']] += t[0]['amount']
        return taxes

    @api.multi
    def get_tax_description(self, tax_line_name):
        tax_line_name_parts = tax_line_name.split('-')
        if len(tax_line_name_parts) > 0:
            return tax_line_name_parts[0]
        else:
            return tax_line_name

    def monetary_format(self, amount):
        cr, uid, context = self.env.args
        company = self.env['res.company'].search([])[0]
        currency = company.currency_id
        lang_code = context.get('lang') or 'en_US'
        lang = self.env['res.lang'].search([('code', '=', lang_code)])
        precision = int(round(math.log10(currency.rounding)))
        fmt = "%.{0}f".format(-precision if precision < 0 else 0)
        formatted_amount = lang.format(
            fmt, currency.round(amount), grouping=True, monetary=True)
        return formatted_amount

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        sale_order_obj = self.env['sale.order']
        report = report_obj._get_report_from_name(
            'print_order_preparation.report_order_preparation')
        selected_sale_orders = sale_order_obj.browse(self.ids)

        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': selected_sale_orders,
            'sort_keys': partial(self.sort_keys),
            'get_order_lines_by_loc': partial(self.get_order_lines_by_loc),
            'get_taxes': partial(self.get_taxes),
            'get_tax_description': partial(self.get_tax_description),
            'monetary_format': partial(self.monetary_format)}

        report = report_obj.browse(self.ids[0])
        return report.render(
            'print_order_preparation.report_order_preparation', docargs)
