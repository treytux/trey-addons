# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests.common import TransactionCase
from openerp import _, exceptions


class PriceUosProductCase(TransactionCase):

    def setUp(self):
        super(PriceUosProductCase, self).setUp()
        self.taxs_21 = self.env['account.tax'].search([
            ('name', 'like', '%21%'),
            ('company_id', '=', self.ref('base.main_company'))])
        if not self.taxs_21.exists():
            raise exceptions.Warning(_(
                'Does not exist any account tax with \'21\' in name.'))
        self.tax_21 = self.taxs_21[0]
        self.uom_categ_01 = self.env['product.uom.categ'].create(
            {'name': 'Surface'})
        self.uom_m2 = self.env['product.uom'].create({
            'name': 'm2',
            'category_id': self.uom_categ_01.id})
        self.uom_mm = self.env['product.uom'].create({
            'name': 'mm',
            'category_id': self.ref('product.uom_categ_length'),
            'factor': 1000,
            'uom_type': 'smaller'})
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'consu',
            'uom_id': self.ref('product.product_uom_unit'),
            'list_price': 10,
            'taxes_id': [(6, 0, [self.tax_21.id])]})
        pp_01_data = {'product_tmpl_id': self.pt_01.id}
        self.pp_01 = self.env['product.product'].create(pp_01_data)

    def test_price_uos_product_no_change_result_zero(self):
        wiz = self.env['wiz.product.config'].with_context({
            'active_ids': [self.pt_01.id],
            'active_model': 'product.template',
            'active_id': self.pt_01.id}).create({
                'dimensional_uom_id': self.uom_mm.id,
                'uos_id': self.uom_m2.id})
        self.assertEqual(wiz.uom_id.id, self.ref('product.product_uom_unit'))
        self.assertEqual(wiz.list_price, 10)
        self.assertEqual(wiz.dimensional_uom_id, self.uom_mm)
        self.assertEqual(wiz.length, 0)
        self.assertEqual(wiz.height, 0)
        self.assertEqual(wiz.width, 0)
        self.assertEqual(wiz.uos_id, self.uom_m2)
        self.assertEqual(wiz.price_unit_uos, 0)
        self.assertEqual(wiz.uos_coeff, 1)
        wiz.button_accept()
        self.pt_01.refresh()
        self.assertEqual(self.pt_01.uom_id.id, self.ref(
            'product.product_uom_unit'))
        self.assertEqual(self.pt_01.price_unit_uos, 0)
        self.assertEqual(self.pt_01.list_price, 10)
        # Not is equals UFO
        # self.assertEqual(self.pt_01.dimensional_uom_id, self.uom_mm)
        self.assertEqual(self.pt_01.length, 0)
        self.assertEqual(self.pt_01.height, 0)
        self.assertEqual(self.pt_01.width, 0)
        self.assertEqual(self.pt_01.uos_id, self.uom_m2)
        self.assertEqual(self.pt_01.uos_coeff, 1)

    def test_price_uos_product_with_coef_not_zero(self):
        wiz = self.env['wiz.product.config'].with_context({
            'active_ids': [self.pt_01.id],
            'active_model': 'product.template',
            'active_id': self.pt_01.id}).create({
                'dimensional_uom_id': self.uom_mm.id,
                'uos_id': self.uom_m2.id,
                'height': 0.88,
                'width': 0.88,
                'price_unit_uos': 0.89})
        self.assertEqual(wiz.uom_id.id, self.ref('product.product_uom_unit'))
        self.assertEqual(wiz.list_price, 10)
        self.assertEqual(wiz.dimensional_uom_id, self.uom_mm)
        self.assertEqual(wiz.length, 0)
        self.assertEqual(wiz.height, 0.88)
        self.assertEqual(wiz.width, 0.88)
        self.assertEqual(wiz.uos_id, self.uom_m2)
        self.assertEqual(wiz.price_unit_uos, 0.89)
        self.assertEqual(wiz.uos_coeff, 1)
        wiz.compute()
        self.assertEqual(wiz.uos_coeff, 0.774)
        self.assertEqual(round(wiz.list_price, 2), 0.69)
        wiz.button_accept()
        self.assertEqual(self.pt_01.uom_id.id, self.ref(
            'product.product_uom_unit'))
        self.assertEqual(self.pt_01.price_unit_uos, 0.89)
        self.assertEqual(self.pt_01.list_price, 0.69)
        # Not is equals UFO
        # self.assertEqual(self.pt_01.dimensional_uom_id, self.uom_mm)
        # self.assertEqual(self.pt_01.height, 0.88)
        # self.assertEqual(self.pt_01.width, 0.88)
        self.assertEqual(self.pt_01.length, 0)
        self.assertEqual(self.pt_01.uos_id, self.uom_m2)
        self.assertEqual(self.pt_01.uos_coeff, 0.774)
