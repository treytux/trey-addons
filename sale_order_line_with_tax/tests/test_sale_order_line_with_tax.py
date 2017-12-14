# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp.tests.common import TransactionCase
from openerp import exceptions, _

import logging
_log = logging.getLogger(__name__)


class SaleOrderLineWithTaxCase(TransactionCase):
    '''Test sale.order.line'''

    def setUp(self):
        '''Create sale order line.'''
        super(SaleOrderLineWithTaxCase, self).setUp()

        self.company = self.browse_ref('base.main_company')
        domain = [
            ('name', '=', 'IVA 21% (Bienes)'),
            ('company_id', '=', self.company.id)]
        taxs = self.env['account.tax'].search(domain)
        if not taxs.exists():
            raise exceptions.Warning(_(
                'Does not exist the tax in company %s.' % (self.company.name)))

        # Crear cliente
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
            'company_id': self.company.id})

        # Crear producto
        self.product = self.env['product.product'].create(
            {'name': 'Product test',
             'type': 'product',
             'list_price': 10,
             'company_id': self.company.id})

        # Crear pedido
        self.so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'order_policy': 'picking'})

        # Crear linea pedido
        self.sol = self.env['sale.order.line'].create({
            'name': '/',
            'order_id': self.so.id,
            'product_id': self.product.id,
            'product_uom_qty': 2,
            'company_id': self.company.id,
            'tax_id': [(6, 0, [t.id for t in taxs])]})

    def test_00_sale_order_line_with_tax(self):
        '''Change quantity in sale order line.'''
        self.sol.product_uom_qty = 1
        self.assertEqual(self.sol.price_with_tax, 12.1)
        self.sol.product_uom_qty = 3
        self.assertEqual(self.sol.price_with_tax, 36.3)
