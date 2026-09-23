###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from unittest.mock import MagicMock, patch

from odoo.addons.website_sale_categorized_features.controllers import \
    website_sale as controller_module
from odoo.tests.common import TransactionCase


class TestProductFeatureValue(TransactionCase):

    def test_name_get_context_show_attribute(self):
        feature = self.env['product.feature'].create({
            'name': 'Color',
        })
        value = self.env['product.feature.value'].create({
            'name': 'Red',
            'feature_id': feature.id,
        })
        with_attr = value.with_context(show_attribute=True).name_get()
        self.assertEqual(with_attr, [[value.id, 'Color: Red']])
        without_attr = value.with_context(show_attribute=False).name_get()
        self.assertEqual(without_attr, [(value.id, 'Red')])

    def test_constraint_duplicate_value(self):
        feature = self.env['product.feature'].create({
            'name': 'Color',
        })
        self.env['product.feature.value'].create({
            'name': 'Red',
            'feature_id': feature.id,
        })
        with self.env.cr.savepoint():
            with self.assertRaises(Exception):
                self.env['product.feature.value'].create({
                    'name': 'Red',
                    'feature_id': feature.id,
                })


class TestWebsiteSale(TransactionCase):

    def test_get_applied_feature_value_ids(self):
        ctrl = controller_module.WebsiteSale()
        cases = [
            (['1-10'], {10}),
            (['1-10', '2-20'], {10, 20}),
            (['1-10', '', 'invalid', '1-', '-5', '1-abc', '3-30'],
             {10, 5, 30}),
            ([], set()),
            (['', 'invalid', '1-', '-5', '1-abc'], {5}),
        ]
        for args, expected in cases:
            mock_request = MagicMock()
            mock_request.httprequest.args.getlist.return_value = args
            with patch.object(controller_module, 'request', mock_request):
                self.assertEqual(
                    ctrl._get_applied_feature_value_ids(), expected)

    def test_get_available_feature_values(self):
        feature_color = self.env['product.feature'].create({
            'name': 'Color',
        })
        feature_size = self.env['product.feature'].create({
            'name': 'Size',
        })
        val_red = self.env['product.feature.value'].create({
            'name': 'Red',
            'feature_id': feature_color.id,
        })
        val_blue = self.env['product.feature.value'].create({
            'name': 'Blue',
            'feature_id': feature_color.id,
        })
        val_s = self.env['product.feature.value'].create({
            'name': 'S',
            'feature_id': feature_size.id,
        })
        val_m = self.env['product.feature.value'].create({
            'name': 'M',
            'feature_id': feature_size.id,
        })
        product = self.env['product.template'].create({
            'name': 'Test Product',
            'feature_line_ids': [
                (0, 0, {
                    'feature_id': feature_color.id,
                    'value_ids': [(4, val_red.id), (4, val_blue.id)],
                }),
                (0, 0, {
                    'feature_id': feature_size.id,
                    'value_ids': [(4, val_s.id)],
                }),
            ],
        })
        mock_request = MagicMock()
        mock_request.env = self.env
        with patch.object(controller_module, 'request', mock_request):
            ctrl = controller_module.WebsiteSale()
            result = ctrl._get_available_feature_values(
                self.env['product.template'].browse(product.id)
            )
        self.assertIn(feature_color.id, result)
        self.assertIn(feature_size.id, result)
        self.assertEqual(
            result[feature_color.id], {val_red.id, val_blue.id})
        self.assertEqual(result[feature_size.id], {val_s.id})
        self.assertNotIn(val_m.id, result.get(feature_size.id, set()))

    def test_shop_filters_features_by_availability(self):
        category = self.env['product.public.category'].create({
            'name': 'Test Category',
        })
        feature_color = self.env['product.feature'].create({
            'name': 'Color',
        })
        feature_size = self.env['product.feature'].create({
            'name': 'Size',
        })
        category.write({
            'feature_ids': [
                (4, feature_color.id), (4, feature_size.id),]
        })
        val_red = self.env['product.feature.value'].create({
            'name': 'Red',
            'feature_id': feature_color.id,
        })
        val_blue = self.env['product.feature.value'].create({
            'name': 'Blue',
            'feature_id': feature_color.id,
        })
        self.env['product.feature.value'].create({
            'name': 'S',
            'feature_id': feature_size.id,
        })
        product = self.env['product.template'].create({
            'name': 'Test Product',
            'public_categ_ids': [(4, category.id)],
            'feature_line_ids': [(0, 0, {
                'feature_id': feature_color.id,
                'value_ids': [(4, val_red.id), (4, val_blue.id)],
            })],
        })
        search_product = self.env['product.template'].browse(product.id)
        ctrl = controller_module.WebsiteSale()
        features = ctrl._get_features(category)
        mock_request = MagicMock()
        mock_request.httprequest.args.getlist.return_value = []
        mock_request.env = self.env
        with patch.object(controller_module, 'request', mock_request):
            features_set = ctrl._get_applied_feature_value_ids()
            available_values = ctrl._get_available_feature_values(
                search_product, features.ids)
            filtered_features = features.filtered(
                lambda f: bool(available_values.get(f.id)))
        self.assertEqual(features_set, set())
        self.assertIn(feature_color, filtered_features)
        self.assertNotIn(feature_size, filtered_features)
        self.assertEqual(
            available_values[feature_color.id], {val_red.id, val_blue.id})
