# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, exceptions, _, api


class WizProductLabelFromPriceHistory(models.TransientModel):
    _inherit = 'wiz.product.label'

    date_from = fields.Datetime(
        string='Date From',
        default=fields.Datetime.now(),
        required=True
    )
    price_history_quantity = fields.Selection(
        string='Quantity',
        selection=[
            ('one', 'One label for each product'),
            ('total', 'Total product stock quantity'),
        ],
        default='one'
    )

    @api.multi
    def button_print_from_price_history(self):
        wiz = self[0]
        price_historys = self.env['product.price.history'].search(
            [('datetime', '>=', wiz.date_from)])
        product_ids = []
        if wiz.price_history_quantity == 'one':
            product_tmpl_ids = [ph.product_template_id.id for ph in
                                price_historys]
            products = self.env['product.product'].search(
                [('product_tmpl_id', 'in', product_tmpl_ids)])
            product_ids = list(set([p.id for p in products]))
        elif wiz.price_history_quantity == 'total':
            for ph in price_historys:
                found_products = self.env['product.product'].search(
                    [('product_tmpl_id', '=', ph.product_template_id.id)],
                    limit=1)
                found_product_ids = [p.id for p in found_products]
                if found_products.exists() \
                   and found_products[0].id not in product_ids:
                    found_product_ids *= int(
                        ph.product_template_id.qty_available)
                    product_ids = product_ids + found_product_ids
        product_ids = filter(lambda x: x, product_ids)
        if not product_ids:
            raise exceptions.Warning(_('No labels for print'))
        else:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': wiz.report_id.report_name,
                'datas': {'ids': product_ids}}
