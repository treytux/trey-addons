###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestWebsiteSaleDescriptionTemplates(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 30,
        })
        self.product_tmpl = self.env['product.template'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product template',
            'standard_price': 10,
            'list_price': 40,
        })
        self.msg = 'Product with name ${object.name}'
        self.template = self.env['product.content.template'].create({
            'name': 'Template test',
            'body_html': self.msg,
        })

    def test_check_set_product_tmpl_content_template(self):
        self.assertFalse(self.product_tmpl.website_description)
        self.assertEqual(self.template.body_html, self.msg)
        action = self.env.ref(
            'website_sale_description_templates.content_template_wzd_action')
        res = self.product_tmpl.action_set_content_template()
        self.assertEqual(action.id, res['id'])
        wizard = self.env['wizard.product.content.template'].with_context(
            active_ids=self.product_tmpl.ids,
            active_id=self.product_tmpl.ids[0],
            active_model='product.template',
        ).create({
            'content_template': self.template.id,
        })
        self.assertEqual(wizard.content_template, self.template)
        wizard.button_set_content_template()
        self.assertEqual(
            self.product_tmpl.website_description,
            '<p>Product with name %s</p>' % self.product_tmpl.name)

    def test_check_set_product_product_content_template(self):
        self.assertFalse(self.product.website_description)
        self.assertEqual(self.template.body_html, self.msg)
        action = self.env.ref(
            'website_sale_description_templates.content_template_wzd_action')
        res = self.product.action_set_content_template()
        self.assertEqual(action.id, res['id'])
        wizard = self.env['wizard.product.content.template'].with_context(
            active_ids=self.product.ids,
            active_id=self.product.ids[0],
            active_model='product.product',
        ).create({
            'content_template': self.template.id,
        })
        self.assertEqual(wizard.content_template, self.template)
        wizard.button_set_content_template()
        self.assertEqual(
            self.product.website_description,
            '<p>Product with name %s</p>' % self.product.name)
