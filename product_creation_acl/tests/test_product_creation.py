###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import common


class TestProductCreation(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_fail_create_product(self):
        """ This test will fail because the user is not in the group """
        with self.assertRaises(ValidationError):
            self.env['product.template'].create({
                'name': 'Test Product',
            })

    def test_create_product(self):
        """ This test will not fail because the user is not in the group """
        group = self.env.ref('product_creation_acl.group_product_creation')
        self.env.user.groups_id = [(4, group.id)]
        self.env['product.template'].create({
            'name': 'Test Partner2',
        })
