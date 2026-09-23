###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestGoodsFreeMassiveCreation(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product 1',
            'standard_price': 10,
            'list_price': 80,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product 2',
            'standard_price': 10,
            'list_price': 60,
        })
        self.product_03 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product 3',
            'standard_price': 10,
            'list_price': 70,
        })
        self.public_categ_01 = self.env['product.public.category'].create({
            'name': 'Test category 1',
        })
        self.public_categ_02 = self.env['product.public.category'].create({
            'name': 'Test category 2',
        })
        self.public_categ_03 = self.env['product.public.category'].create({
            'name': 'Test category 3',
        })
        self.season_01 = self.env['product.season'].create({
            'name': 'Season test 1',
        })
        self.season_02 = self.env['product.season'].create({
            'name': 'Season test 2',
        })
        self.season_03 = self.env['product.season'].create({
            'name': 'Season test 3',
        })
        self.product_01.write({
            'season_id': self.season_01.id,
            'public_categ_ids': [
                (6, 0, [self.public_categ_01.id, self.public_categ_03.id]),
            ],
        })
        self.product_02.write({
            'season_id': self.season_02.id,
            'public_categ_ids': [
                (6, 0, [self.public_categ_02.id, self.public_categ_03.id]),
            ],
        })
        self.product_03.write({
            'season_id': self.season_01.id,
            'public_categ_ids': [
                (6, 0, [self.public_categ_02.id]),
            ],
        })

    def test_goods_free_massive_action_ok_01(self):
        self.assertEqual(len(self.partner.goods_free_ids), 0)
        wizard = self.env['goods_free.mass.create'].create({
            'partner_id': self.partner.id,
            'percent': 10,
        })
        self.assertEqual(wizard.partner_id, self.partner)
        self.assertEqual(wizard.percent, 10)
        wizard.write({
            'season_id': self.season_01.id,
            'categ_ids': [
                (6, 0, [self.public_categ_01.id, self.public_categ_02.id])],
        })
        self.assertEqual(wizard.season_id, self.season_01)
        self.assertIn(self.public_categ_01.id, wizard.categ_ids.ids)
        self.assertIn(self.public_categ_02.id, wizard.categ_ids.ids)
        wizard.button_create_goods_free()
        self.assertEqual(len(self.partner.goods_free_ids), 2)
        self.assertIn(
            self.product_01.id,
            self.partner.goods_free_ids.mapped('product_id').ids)
        self.assertNotIn(
            self.product_02.id,
            self.partner.goods_free_ids.mapped('product_id').ids)
        self.assertIn(
            self.product_03.id,
            self.partner.goods_free_ids.mapped('product_id').ids)

    def test_goods_free_massive_action_website_sale_category_only_02(self):
        self.assertEqual(len(self.partner.goods_free_ids), 0)
        wizard = self.env['goods_free.mass.create'].create({
            'partner_id': self.partner.id,
            'percent': 10,
        })
        self.assertEqual(wizard.partner_id, self.partner)
        self.assertEqual(wizard.percent, 10)
        wizard.write({
            'categ_ids': [
                (6, 0, [self.public_categ_01.id, self.public_categ_03.id])],
        })
        self.assertFalse(wizard.season_id)
        self.assertEqual(len(wizard.categ_ids), 2)
        self.assertIn(self.public_categ_01.id, wizard.categ_ids.ids)
        self.assertIn(self.public_categ_03.id, wizard.categ_ids.ids)
        wizard.button_create_goods_free()
        self.assertEqual(len(self.partner.goods_free_ids), 2)
        self.assertIn(
            self.product_01.id,
            self.partner.goods_free_ids.mapped('product_id').ids)
        self.assertIn(
            self.product_02.id,
            self.partner.goods_free_ids.mapped('product_id').ids)
        self.assertNotIn(
            self.product_03.id,
            self.partner.goods_free_ids.mapped('product_id').ids)

    def test_goods_free_massive_action_season_only_03(self):
        self.assertEqual(len(self.partner.goods_free_ids), 0)
        wizard = self.env['goods_free.mass.create'].create({
            'partner_id': self.partner.id,
            'percent': 10,
        })
        self.assertEqual(wizard.partner_id, self.partner)
        self.assertEqual(wizard.percent, 10)
        wizard.write({
            'season_id': self.season_02.id,
        })
        self.assertEqual(wizard.season_id, self.season_02)
        self.assertEqual(len(wizard.categ_ids), 0)
        wizard.button_create_goods_free()
        self.assertEqual(len(self.partner.goods_free_ids), 1)
        self.assertIn(
            self.product_02.id,
            self.partner.goods_free_ids.mapped('product_id').ids)
        self.assertNotIn(
            self.product_01.id,
            self.partner.goods_free_ids.mapped('product_id').ids)
        self.assertNotIn(
            self.product_03.id,
            self.partner.goods_free_ids.mapped('product_id').ids)

    def test_goods_free_massive_action_error_incomplete_fields_05(self):
        self.assertEqual(len(self.partner.goods_free_ids), 0)
        wizard = self.env['goods_free.mass.create'].create({
            'partner_id': self.partner.id,
            'percent': 10,
        })
        self.assertEqual(wizard.partner_id, self.partner)
        self.assertEqual(wizard.percent, 10)
        self.assertFalse(wizard.season_id)
        self.assertFalse(wizard.categ_ids)
        goods_free_01 = len(self.partner.goods_free_ids)
        wizard.button_create_goods_free()
        self.assertEqual(wizard.step, 2)
        wizard.button_create_goods_free_all_products()
        self.assertEqual(wizard.step, 1)
        goods_free_02 = len(self.partner.goods_free_ids)
        self.assertNotEqual(goods_free_01, goods_free_02)
        products = self.env['product.product'].search([])
        self.assertEqual(goods_free_02, len(products))
        self.assertEqual(
            goods_free_02, len(products) + goods_free_01)

    def test_goods_free_massive_new_update_01(self):
        self.assertEqual(len(self.partner.goods_free_ids), 0)
        self.env['res.partner.goods_free'].create({
            'partner_id': self.partner.id,
            'product_id': self.product_01.id,
            'percent': 20,
        })
        self.env['res.partner.goods_free'].create({
            'partner_id': self.partner.id,
            'product_id': self.product_03.id,
            'percent': 20,
        })
        self.assertEqual(len(self.partner.goods_free_ids), 2)
        self.assertEqual(
            self.partner.goods_free_ids[0].partner_id, self.partner)
        self.assertEqual(
            self.partner.goods_free_ids[1].partner_id, self.partner)
        self.assertEqual(
            self.partner.goods_free_ids[0].product_id, self.product_01)
        self.assertEqual(
            self.partner.goods_free_ids[1].product_id, self.product_03)
        goods_free_old = self.partner.goods_free_ids
        percent_old_01 = self.partner.goods_free_ids[0].percent
        percent_old_02 = self.partner.goods_free_ids[1].percent
        wizard = self.env['goods_free.mass.create'].create({
            'partner_id': self.partner.id,
            'percent': 10,
        })
        self.assertEqual(wizard.partner_id, self.partner)
        self.assertEqual(wizard.percent, 10)
        wizard.write({
            'season_id': self.season_01.id,
            'categ_ids': [
                (6, 0, [self.public_categ_01.id, self.public_categ_02.id])],
        })
        self.assertEqual(wizard.season_id, self.season_01)
        self.assertIn(self.public_categ_01.id, wizard.categ_ids.ids)
        self.assertIn(self.public_categ_02.id, wizard.categ_ids.ids)
        wizard.button_create_goods_free()
        self.assertEqual(len(self.partner.goods_free_ids), 2)
        self.assertIn(
            self.product_01.id,
            self.partner.goods_free_ids.mapped('product_id').ids)
        self.assertNotIn(
            self.product_02.id,
            self.partner.goods_free_ids.mapped('product_id').ids)
        self.assertIn(
            self.product_03.id,
            self.partner.goods_free_ids.mapped('product_id').ids)
        self.assertEqual(goods_free_old[0], self.partner.goods_free_ids[0])
        self.assertEqual(goods_free_old[1], self.partner.goods_free_ids[1])
        self.assertNotEqual(
            percent_old_01, self.partner.goods_free_ids[0].percent)
        self.assertNotEqual(
            percent_old_02, self.partner.goods_free_ids[1].percent)

    def test_goods_free_massive_new_update_02(self):
        self.assertEqual(len(self.partner.goods_free_ids), 0)
        self.env['res.partner.goods_free'].create({
            'partner_id': self.partner.id,
            'product_id': self.product_01.id,
            'percent': 10,
        })
        self.env['res.partner.goods_free'].create({
            'partner_id': self.partner.id,
            'product_id': self.product_03.id,
            'percent': 20,
        })
        self.assertEqual(len(self.partner.goods_free_ids), 2)
        self.assertEqual(
            self.partner.goods_free_ids[0].partner_id, self.partner)
        self.assertEqual(
            self.partner.goods_free_ids[1].partner_id, self.partner)
        self.assertEqual(
            self.partner.goods_free_ids[0].product_id, self.product_01)
        self.assertEqual(
            self.partner.goods_free_ids[1].product_id, self.product_03)
        goods_free_old = self.partner.goods_free_ids
        percent_old_01 = self.partner.goods_free_ids[0].percent
        percent_old_02 = self.partner.goods_free_ids[1].percent
        wizard = self.env['goods_free.mass.create'].create({
            'partner_id': self.partner.id,
            'percent': 10,
        })
        self.assertEqual(wizard.partner_id, self.partner)
        self.assertEqual(wizard.percent, 10)
        wizard.write({
            'season_id': self.season_01.id,
            'categ_ids': [
                (6, 0, [self.public_categ_01.id, self.public_categ_02.id])],
        })
        self.assertEqual(wizard.season_id, self.season_01)
        self.assertIn(self.public_categ_01.id, wizard.categ_ids.ids)
        self.assertIn(self.public_categ_02.id, wizard.categ_ids.ids)
        wizard.button_create_goods_free()
        self.assertEqual(len(self.partner.goods_free_ids), 2)
        self.assertIn(
            self.product_01.id,
            self.partner.goods_free_ids.mapped('product_id').ids)
        self.assertNotIn(
            self.product_02.id,
            self.partner.goods_free_ids.mapped('product_id').ids)
        self.assertIn(
            self.product_03.id,
            self.partner.goods_free_ids.mapped('product_id').ids)
        self.assertEqual(goods_free_old[0], self.partner.goods_free_ids[0])
        self.assertEqual(goods_free_old[1], self.partner.goods_free_ids[1])
        self.assertNotEqual(
            percent_old_02, self.partner.goods_free_ids[0].percent)
        self.assertEqual(
            percent_old_01, self.partner.goods_free_ids[1].percent)
