###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSaleCommentTemplateTermsConditions(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Test partner 01',
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product 01',
            'standard_price': 10,
            'list_price': 30,
        })

    def test_condition_unique(self):
        sale_model_obj = self.env.ref('sale.model_sale_order')
        comment_01 = self.env['base.comment.template'].create({
            'name': 'Comment',
            'text': 'Text before lines',
            'model_ids': [(4, sale_model_obj.id)],
        })
        condition_01 = self.env['base.comment.template'].create({
            'name': 'Terms and Conditions 01',
            'text': 'Text before lines',
            'is_condition': True,
            'model_ids': [(4, sale_model_obj.id)],
        })
        condition_02 = self.env['base.comment.template'].create({
            'name': 'Terms and Conditions 02',
            'text': 'Text before lines',
            'is_condition': True,
            'model_ids': [(4, sale_model_obj.id)],
        })
        sale_01 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 100,
                    'product_uom_qty': 5,
                }),
            ],
        })
        sale_01.comment_template_ids = [
            (6, 0, [comment_01.id, condition_01.id])]
        self.assertEqual(len(sale_01.comment_template_ids), 2)
        with self.assertRaises(ValidationError):
            sale_01.comment_template_ids = [(4, condition_02.id)]
