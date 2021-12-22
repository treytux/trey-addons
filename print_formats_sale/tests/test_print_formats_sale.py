###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import os

from odoo import tools
from odoo.tests.common import HttpCase


class TestPrintFormatsSale(HttpCase):

    def setUp(self):
        super().setUp()
        self.customer = self.env['res.partner'].create({
            'name': 'Test customer 1',
            'customer': True,
            'company_id': False,
        })
        self.product1 = self.env['product.product'].create({
            'name': 'Test product 1',
            'type': 'service',
            'standard_price': 90,
            'list_price': 100,
            'company_id': False,
        })

    def create_sale_order(self, partner, product, qty):
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_invoice_id': partner.id,
            'partner_shipping_id': partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        sale.onchange_partner_id()
        vline = self.env['sale.order.line'].new({
            'order_id': sale.id,
            'name': product.name,
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'price_unit': product.list_price,
        })
        vline.product_id_change()
        self.env['sale.order.line'].create(
            vline._convert_to_write(vline._cache))
        return sale

    def print_report(self, records, report_action):
        pdf = report_action.with_context(
            force_report_rendering=True).render_qweb_pdf(records.ids)[0]
        fname = os.path.join(
            tools.config['data_dir'], '%s.pdf' % report_action.report_file)
        import logging
        _log = logging.getLogger(__name__)
        _log.info('X' * 80)
        _log.info(('fname', fname))
        _log.info('X' * 80)
        with open(fname, 'bw') as fp:
            fp.write(pdf)

    def test_print_report(self):
        sale = self.create_sale_order(self.customer, self.product1, 66)
        report_action = self.env.ref('sale.action_report_saleorder')
        self.print_report(sale, report_action)
