###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductTemplateMaintenance(TransactionCase):
    def setUp(self):
        super().setUp()

    def test_product_template_is_maintenance(self):
        template = self.env['product.template'].create({
            'name': 'Maintenance Service',
            'type': 'service',
            'is_maintenance': True,
        })
        self.assertTrue(template.is_maintenance)
        self.assertEqual(len(template.product_variant_ids), 1)
        self.assertTrue(template.product_variant_id.is_maintenance)
