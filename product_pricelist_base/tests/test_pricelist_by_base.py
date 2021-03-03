###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.tools import float_compare, test_reports


class TestPricelistByBase(TransactionCase):

    def setUp(self):
        super().setUp()
        self.datacard = self.env.ref('product.product_delivery_02')
        self.usb_adapter = self.env.ref('product.product_delivery_01')
        self.uom_ton = self.env.ref('uom.product_uom_ton')
        self.uom_unit_id = self.ref('uom.product_uom_unit')
        self.uom_dozen_id = self.ref('uom.product_uom_dozen')
        self.uom_kgm_id = self.ref('uom.product_uom_kgm')
        self.public_pricelist = self.env.ref('product.list0')
        self.sale_pricelist_id = self.env['product.pricelist'].create({
            'name': 'Sale pricelist',
            'item_ids': [
                (0, 0, {
                    'compute_price': 'formula',
                    'base': 'list_price',
                    'price_discount': 10,
                    'product_id': self.usb_adapter.id,
                    'applied_on': '0_product_variant',
                }),
                (0, 0, {
                    'compute_price': 'formula',
                    'base': 'list_price',
                    'price_surcharge': -0.5,
                    'product_id': self.datacard.id,
                    'applied_on': '0_product_variant',
                }),
            ],
        })
        self.ProductPricelist = self.env['product.pricelist']
        self.res_partner_4 = self.env.ref('base.res_partner_4')
        self.computer_SC234 = self.env.ref('product.product_product_3')
        self.ipad_retina_display = self.env.ref('product.product_product_4')
        self.custom_computer_kit = self.env.ref('product.product_product_5')
        self.ipad_mini = self.env.ref('product.product_product_6')
        self.apple_in_ear_headphones = self.env.ref(
            'product.product_product_7')
        self.laptop_E5023 = self.env.ref('product.product_delivery_01')
        self.laptop_S3450 = self.env.ref('product.product_product_25')
        self.category_5_id = self.ref('product.product_category_5')
        self.uom_unit_id = self.ref('uom.product_uom_unit')
        self.list0 = self.ref('product.list0')
        self.ipad_retina_display.write({
            'uom_id': self.uom_unit_id, 'categ_id': self.category_5_id})
        self.customer_pricelist = self.ProductPricelist.create({
            'name': 'Customer Pricelist',
            'item_ids': [(0, 0, {
                'name': 'Default pricelist',
                'compute_price': 'formula',
                'base': 'pricelist',
                'base_pricelist_id': self.list0
            }), (0, 0, {
                'name': '10% Discount on Assemble Computer',
                'applied_on': '1_product',
                'product_id': self.ipad_retina_display.id,
                'compute_price': 'formula',
                'base': 'list_price',
                'price_discount': 10
            }), (0, 0, {
                'name': '1 surchange on Laptop',
                'applied_on': '1_product',
                'product_id': self.laptop_E5023.id,
                'compute_price': 'formula',
                'base': 'list_price',
                'price_surcharge': 1
            }), (0, 0, {
                'name': '5% Discount on all Computer related products',
                'applied_on': '2_product_category',
                'min_quantity': 2,
                'compute_price': 'formula',
                'base': 'list_price',
                'categ_id': self.category_5_id,
                'price_discount': 5
            }), (0, 0, {
                'name': '30% Discount on all products',
                'applied_on': '0_product_variant',
                'date_start': '2011-12-27',
                'date_end': '2011-12-31',
                'compute_price': 'formula',
                'price_discount': 30,
                'base': 'list_price'
            })]
        })

    def test_10_discount(self):
        context = {}
        public_context = dict(context, pricelist=self.public_pricelist.id)
        pricelist_context = dict(context, pricelist=self.sale_pricelist_id.id)
        usb_adapter_without_pricelist = self.usb_adapter.with_context(
            public_context)
        usb_adapter_with_pricelist = self.usb_adapter.with_context(
            pricelist_context)
        self.assertEqual(
            usb_adapter_with_pricelist.price,
            usb_adapter_without_pricelist.price * 0.9)
        datacard_without_pricelist = self.datacard.with_context(public_context)
        datacard_with_pricelist = self.datacard.with_context(pricelist_context)
        self.assertEqual(
            datacard_with_pricelist.price,
            datacard_without_pricelist.price - 0.5)
        unit_context = dict(
            context, pricelist=self.sale_pricelist_id.id, uom=self.uom_unit_id)
        dozen_context = dict(
            context,
            pricelist=self.sale_pricelist_id.id, uom=self.uom_dozen_id)
        usb_adapter_unit = self.usb_adapter.with_context(unit_context)
        usb_adapter_dozen = self.usb_adapter.with_context(dozen_context)
        self.assertAlmostEqual(
            usb_adapter_unit.price * 12, usb_adapter_dozen.price)
        datacard_unit = self.datacard.with_context(unit_context)
        datacard_dozen = self.datacard.with_context(dozen_context)
        self.assertAlmostEqual(datacard_unit.price * 12, datacard_dozen.price)

    def test_20_pricelist_uom(self):
        kg, tonne = self.uom_kgm_id, self.uom_ton.id
        tonne_price = 100
        self.uom_ton.write({'rounding': 0.001})
        spam_id = self.usb_adapter.copy({
            'name': '1 tonne of spam',
            'uom_id': self.uom_ton.id,
            'uom_po_id': self.uom_ton.id,
            'list_price': tonne_price,
            'type': 'consu',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': self.public_pricelist.id,
            'applied_on': '0_product_variant',
            'compute_price': 'formula',
            'base': 'list_price',
            'min_quantity': 3,
            'price_surcharge': -10,
            'product_id': spam_id.id,
        })
        pricelist = self.public_pricelist

        def test_unit_price(qty, uom, expected_unit_price):
            spam = spam_id.with_context({'uom': uom})
            unit_price = pricelist.with_context(
                {'uom': uom}).get_product_price(spam, qty, False)
            self.assertAlmostEqual(
                unit_price, expected_unit_price,
                msg='Computed unit price is wrong')

        test_unit_price(2, kg, tonne_price / 1000.0)
        test_unit_price(2000, kg, tonne_price / 1000.0)
        test_unit_price(3500, kg, (tonne_price - 10) / 1000.0)
        test_unit_price(2, tonne, tonne_price)
        test_unit_price(3, tonne, tonne_price - 10)

    def test_10_calculation_price_of_products_pricelist(self):
        context = {}
        context.update(
            {'pricelist': self.customer_pricelist.id, 'quantity': 1})
        ipad_retina_display = self.ipad_retina_display.with_context(context)
        ipad_retina_display_price = (
            ipad_retina_display.lst_price
            - ipad_retina_display.lst_price
            * (0.10)
        )
        msg = (
            'Wrong sale price: Customizable Desk. should be %s '
            'instead of %s' % (
                ipad_retina_display.price, ipad_retina_display_price))
        self.assertEqual(
            float_compare(
                ipad_retina_display.price,
                ipad_retina_display_price,
                precision_digits=2), 0, msg)
        laptop_E5023 = self.laptop_E5023.with_context(context)
        msg = 'Wrong sale price: Laptop. should be %s instead of %s' % (
            laptop_E5023.price, (laptop_E5023.lst_price + 1))
        self.assertEqual(
            float_compare(
                laptop_E5023.price,
                laptop_E5023.lst_price + 1,
                precision_digits=2), 0, msg)
        apple_headphones = self.apple_in_ear_headphones.with_context(context)
        msg = 'Wrong sale price: IT component. should be %s instead of %s' % (
            apple_headphones.price, apple_headphones.lst_price)
        self.assertEqual(
            float_compare(
                apple_headphones.price,
                apple_headphones.lst_price,
                precision_digits=2), 0, msg)
        context.update({'quantity': 5})
        laptop_S3450 = self.laptop_S3450.with_context(context)
        msg = (
            'Wrong sale price: IT component if more than 3 Unit. should be %s '
            'instead of %s' % (
                laptop_S3450.price,
                (laptop_S3450.lst_price - laptop_S3450.lst_price * (0.05))))
        self.assertEqual(
            float_compare(
                laptop_S3450.price,
                laptop_S3450.lst_price - laptop_S3450.lst_price * (0.05),
                precision_digits=2), 0, msg)
        context.update({'quantity': 1})
        ipad_mini = self.ipad_mini.with_context(context)
        msg = 'Wrong sale price: LCD Monitor. should be %s instead of %s' % (
            ipad_mini.price, ipad_mini.lst_price)
        self.assertEqual(float_compare(
            ipad_mini.price, ipad_mini.lst_price, precision_digits=2), 0, msg)
        context.update({'quantity': 1, 'date': '2011-12-31'})
        ipad_mini = self.ipad_mini.with_context(context)
        msg = (
            'Wrong sale price: LCD Monitor on end of year. should be %s '
            'instead of %s' % (
                ipad_mini.price,
                ipad_mini.lst_price - ipad_mini.lst_price * (0.30))
        )
        self.assertEqual(
            float_compare(
                ipad_mini.price,
                ipad_mini.lst_price - ipad_mini.lst_price * (0.30),
                precision_digits=2), 0, msg)
        context.update({
            'quantity': 1, 'date': False, 'partner_id': self.res_partner_4.id})
        ipad_mini = self.ipad_mini.with_context(context)
        partner = self.res_partner_4.with_context(context)
        ipad_mini_price = ipad_mini._select_seller(
            partner_id=partner, quantity=1.0).price
        msg = (
            'Wrong cost price: LCD Monitor. should be 790 instead '
            'of %s' % ipad_mini_price)
        self.assertEqual(
            float_compare(ipad_mini_price, 790, precision_digits=2), 0, msg)
        context.update({'quantity': 3})
        ipad_mini = self.ipad_mini.with_context(context)
        partner = self.res_partner_4.with_context(context)
        ipad_mini_price = ipad_mini._select_seller(
            partner_id=partner, quantity=3.0).price
        msg = (
            'Wrong cost price: LCD Monitor if more than 3 Unit.should be 785 '
            'instead of %s' % ipad_mini_price)
        self.assertEqual(
            float_compare(ipad_mini_price, 785, precision_digits=2), 0, msg)
        ctx = {
            'active_model': 'product.product',
            'date': '2011-12-30',
            'active_ids': [
                self.computer_SC234.id,
                self.ipad_retina_display.id,
                self.custom_computer_kit.id,
                self.ipad_mini.id,
            ]
        }
        data_dict = {
            'qty1': 1,
            'qty2': 5,
            'qty3': 10,
            'qty4': 15,
            'qty5': 30,
            'price_list': self.customer_pricelist.id,
        }
        test_reports.try_report_action(
            self.cr, self.uid, 'action_product_price_list',
            wiz_data=data_dict, context=ctx, our_module='product')
