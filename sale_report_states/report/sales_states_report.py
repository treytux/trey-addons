###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models
from odoo.exceptions import ValidationError
import datetime


class SaleStatesReport(models.AbstractModel):
    _name = 'report.sale_report_states.report_sale_states'

    @api.model
    def _get_customers(self, customers_domain):
        return self.env['res.partner'].search(customers_domain)

    @api.model
    def get_month_labels(self):
        months_labels = {}
        for month in range(1, 12 + 1, 1):
            months_labels[month] = str.capitalize(datetime.date(
                1900, month, 1).strftime('%B'))
        months = sorted(months_labels)
        return [months_labels[key] for key in months]

    @api.model
    def _get_info_grouped_by_state(self, customers, sales_domain):
        months = {
            '01': False, '02': False, '03': False,
            '04': False, '05': False, '06': False,
            '07': False, '08': False, '09': False,
            '10': False, '11': False, '12': False}
        sales = {
            'totals': {
                'total_months': months.copy(),
                'total': False}}
        for customer in customers:
            state = sales.setdefault(
                customer.state_id, {
                    'partner_ids': {},
                    'total_months_state': months.copy(),
                    'total_state': False})
            state['partner_ids'].setdefault(
                customer.commercial_partner_id, {
                    'ref': customer.ref,
                    'sale_months': months.copy(),
                    'total_sale': False})
            partner_domain = [('partner_id', '=', customer.id)]
            sales_customer = self.env['sale.order'].search(
                sales_domain + partner_domain)
            for sale in sales_customer:
                month = sale.confirmation_date[5:7]
                state['total_months_state'][month] += sale.amount_untaxed
                state['total_state'] += sale.amount_untaxed
                state['partner_ids'][sale.partner_id.commercial_partner_id][
                    'sale_months'][month] += sale.amount_untaxed
                state['partner_ids'][sale.partner_id.commercial_partner_id][
                    'total_sale'] += sale.amount_untaxed
                sales['totals']['total_months'][month] += sale.amount_untaxed
                sales['totals']['total'] += sale.amount_untaxed
        return sales

    @api.model
    def get_report_values(self, doc_ids, data=None):
        if not data:
            raise ValidationError('You can not launch this report from here!')
        data['states'] = self.env['res.country.state'].browse(
            data['state_ids'])
        customers_domain = [
            ('ref', '!=', False),
            '|',
            ('customer', '=', True),
            ('parent_id.customer', '=', True),
        ]
        sales_dom = [('state', 'in', ['sale', 'done']),
                     ('confirmation_date', '>=', data['date_from']),
                     ('confirmation_date', '<=', data['date_to'])]
        if data.get('state_ids'):
            customers_domain += [('state_id', 'in', data['state_ids'])]
        if data.get('agent_id'):
            sales_dom += [('partner_id.agents', '=', data['agent_id'])]
            data['agent_name'] = self.env['res.partner'].browse(
                data['agent_id']).name
        if data.get('pricelist_id'):
            sales_dom += [('pricelist_id', '=', data['pricelist_id'])]
            data['pricelist'] = self.env['product.pricelist'].browse(
                data['pricelist_id']).name
        customers = self._get_customers(customers_domain)
        info_by_state = self._get_info_grouped_by_state(customers, sales_dom)
        if not info_by_state:
            raise ValidationError('No results found!')
        report = self.env['ir.actions.report']._get_report_from_name(
            'sale_report_procinces.report_sale_states')
        return {
            'doc_ids': doc_ids,
            'doc_model': report.model,
            'data': data,
            'info_by_state': info_by_state,
            'months_labels': self.get_month_labels()}
