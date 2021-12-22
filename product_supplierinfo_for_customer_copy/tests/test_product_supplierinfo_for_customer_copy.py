###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests import common


class TestProductSupplierinfoForCustomerCopy(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_1 = self.env['res.partner'].create({
            'name': 'Test partner 1',
            'is_company': True,
            'customer': True,
        })
        self.partner_2 = self.env['res.partner'].create({
            'name': 'Test partner 2',
            'is_company': True,
            'customer': True,
        })
        self.product_1 = self.env['product.product'].create({
            'type': 'consu',
            'name': 'Test product 1',
            'standard_price': 10,
            'list_price': 100,
            'default_code': 'TEST01',
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'consu',
            'name': 'Test product 2',
            'standard_price': 5,
            'list_price': 50,
            'default_code': 'TEST02',
        })

    def test_copy_one_customerinfo(self):
        self.env['product.customerinfo'].create({
            'name': self.partner_1.id,
            'product_id': self.product_1.id,
            'product_tmpl_id': self.product_1.product_tmpl_id.id,
            'sequence': 1,
            'product_name': self.product_1.name,
            'product_code': self.product_1.default_code,
            'min_qty': 5,
            'delay': 2,
            'price': 8,
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(months=1),
        })
        len_product_customerinfo1 = self.env['product.customerinfo'].search([])
        product_customerinfos = self.env['product.customerinfo'].search([
            ('name', '=', self.partner_1.id),
            ('product_tmpl_id', '=', self.product_1.product_tmpl_id.id),
            ('product_name', '=', self.product_1.name),
            ('product_code', '=', self.product_1.default_code),
        ])
        self.assertEqual(len(product_customerinfos), 1)
        product_customerinfo_1 = product_customerinfos[0]
        wizard = self.env['product.customerinfo.copy'].with_context(
            active_ids=product_customerinfo_1.id).create({
                'partner_id': self.partner_2.id,
            })
        self.assertEqual(wizard.partner_id.id, self.partner_2.id)
        self.assertEqual(len(wizard.line_ids), 1)
        wizard_line = wizard.line_ids[0]
        self.assertEqual(wizard_line.wizard_id.id, wizard.id)
        self.assertEqual(
            wizard_line.partner_id.id, product_customerinfo_1.name.id)
        self.assertEqual(
            wizard_line.product_tmpl_id.id,
            product_customerinfo_1.product_tmpl_id.id)
        self.assertEqual(
            wizard_line.product_id.id, product_customerinfo_1.product_id.id)
        self.assertEqual(wizard_line.sequence, product_customerinfo_1.sequence)
        self.assertEqual(
            wizard_line.product_name, product_customerinfo_1.product_name)
        self.assertEqual(
            wizard_line.product_code, product_customerinfo_1.product_code)
        self.assertEqual(wizard_line.min_qty, product_customerinfo_1.min_qty)
        self.assertEqual(wizard_line.price, product_customerinfo_1.price)
        self.assertEqual(wizard_line.delay, product_customerinfo_1.delay)
        self.assertEqual(
            wizard_line.date_start, product_customerinfo_1.date_start)
        self.assertEqual(
            wizard_line.date_end, product_customerinfo_1.date_end)
        result = wizard.button_accept()
        len_product_customerinfo2 = self.env['product.customerinfo'].search([])
        self.assertEqual(
            len(len_product_customerinfo2), len(len_product_customerinfo1) + 1)
        self.assertEqual(result['name'], 'Product customer info created')
        product_customerinfos = self.env['product.customerinfo'].search([
            ('name', '=', self.partner_2.id),
            ('product_tmpl_id', '=', self.product_1.product_tmpl_id.id),
            ('product_name', '=', self.product_1.name),
            ('product_code', '=', self.product_1.default_code),
        ])
        self.assertEqual(len(product_customerinfos), 1)
        product_customerinfo_2 = product_customerinfos[0]
        self.assertEqual(product_customerinfo_2.name.id, self.partner_2.id)
        self.assertNotEqual(
            product_customerinfo_2.name, product_customerinfo_1.name)
        self.assertEqual(
            product_customerinfo_2.product_tmpl_id,
            product_customerinfo_1.product_tmpl_id)
        self.assertEqual(
            product_customerinfo_2.product_id,
            product_customerinfo_1.product_id)
        self.assertEqual(
            product_customerinfo_2.sequence, product_customerinfo_1.sequence)
        self.assertEqual(
            product_customerinfo_2.product_name,
            product_customerinfo_1.product_name)
        self.assertEqual(
            product_customerinfo_2.product_code,
            product_customerinfo_1.product_code)
        self.assertEqual(
            product_customerinfo_2.min_qty, product_customerinfo_1.min_qty)
        self.assertEqual(
            product_customerinfo_2.delay, product_customerinfo_1.delay)
        self.assertEqual(
            product_customerinfo_2.price, product_customerinfo_1.price)
        self.assertEqual(
            product_customerinfo_2.date_start,
            product_customerinfo_1.date_start)
        self.assertEqual(
            product_customerinfo_2.date_start,
            product_customerinfo_1.date_start)

    def test_copy_multiple_customerinfo(self):
        self.env['product.customerinfo'].create({
            'name': self.partner_1.id,
            'product_id': self.product_1.id,
            'product_tmpl_id': self.product_1.product_tmpl_id.id,
            'sequence': 1,
            'product_name': self.product_1.name,
            'product_code': self.product_1.default_code,
            'min_qty': 5,
            'delay': 2,
            'price': 8,
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(months=1),
        })
        self.env['product.customerinfo'].create({
            'name': self.partner_1.id,
            'product_id': self.product_2.id,
            'product_tmpl_id': self.product_2.product_tmpl_id.id,
            'sequence': 2,
            'product_name': self.product_2.name,
            'product_code': self.product_2.default_code,
            'min_qty': 8,
            'delay': 1,
            'price': 3,
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(months=1),
        })
        len_product_customerinfo1 = self.env['product.customerinfo'].search([])
        product_customerinfos = self.env['product.customerinfo'].search([
            ('name', '=', self.partner_1.id),
        ])
        self.assertEqual(len(product_customerinfos), 2)
        self.assertEqual(product_customerinfos[0].name.id, self.partner_1.id)
        self.assertEqual(
            product_customerinfos[0].product_tmpl_id.id,
            self.product_1.product_tmpl_id.id)
        self.assertEqual(
            product_customerinfos[0].product_id.id,
            self.product_1.id)
        self.assertEqual(product_customerinfos[0].sequence, 1)
        self.assertEqual(
            product_customerinfos[0].product_name, self.product_1.name)
        self.assertEqual(
            product_customerinfos[0].product_code, self.product_1.default_code)
        self.assertEqual(product_customerinfos[0].min_qty, 5)
        self.assertEqual(product_customerinfos[0].delay, 2)
        self.assertEqual(product_customerinfos[0].price, 8)
        self.assertEqual(
            product_customerinfos[0].date_start, fields.Date.today())
        self.assertEqual(
            product_customerinfos[0].date_end,
            fields.Date.today() + relativedelta(months=1))
        self.assertEqual(product_customerinfos[1].name.id, self.partner_1.id)
        self.assertEqual(
            product_customerinfos[1].product_tmpl_id.id,
            self.product_2.product_tmpl_id.id)
        self.assertEqual(
            product_customerinfos[1].product_id.id,
            self.product_2.id)
        self.assertEqual(product_customerinfos[1].sequence, 2)
        self.assertEqual(
            product_customerinfos[1].product_name, self.product_2.name)
        self.assertEqual(
            product_customerinfos[1].product_code, self.product_2.default_code)
        self.assertEqual(product_customerinfos[1].min_qty, 8)
        self.assertEqual(product_customerinfos[1].delay, 1)
        self.assertEqual(product_customerinfos[1].price, 3)
        self.assertEqual(
            product_customerinfos[1].date_start, fields.Date.today())
        self.assertEqual(
            product_customerinfos[1].date_end,
            fields.Date.today() + relativedelta(months=1))
        wizard = self.env['product.customerinfo.copy'].with_context(
            active_ids=product_customerinfos.ids).create({
                'partner_id': self.partner_2.id,
            })
        self.assertEqual(wizard.partner_id.id, self.partner_2.id)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(
            wizard.line_ids[0].partner_id.id, product_customerinfos[0].name.id)
        self.assertEqual(
            wizard.line_ids[0].product_tmpl_id.id,
            product_customerinfos[0].product_tmpl_id.id)
        self.assertEqual(
            wizard.line_ids[0].product_id.id,
            product_customerinfos[0].product_id.id)
        self.assertEqual(
            wizard.line_ids[0].sequence, product_customerinfos[0].sequence)
        self.assertEqual(
            wizard.line_ids[0].product_name,
            product_customerinfos[0].product_name)
        self.assertEqual(
            wizard.line_ids[0].product_code,
            product_customerinfos[0].product_code)
        self.assertEqual(
            wizard.line_ids[0].min_qty, product_customerinfos[0].min_qty)
        self.assertEqual(
            wizard.line_ids[0].price, product_customerinfos[0].price)
        self.assertEqual(
            wizard.line_ids[0].delay, product_customerinfos[0].delay)
        self.assertEqual(
            wizard.line_ids[0].date_start, product_customerinfos[0].date_start)
        self.assertEqual(
            wizard.line_ids[0].date_end, product_customerinfos[0].date_end)
        self.assertEqual(
            wizard.line_ids[1].partner_id.id, product_customerinfos[1].name.id)
        self.assertEqual(
            wizard.line_ids[1].product_tmpl_id.id,
            product_customerinfos[1].product_tmpl_id.id)
        self.assertEqual(
            wizard.line_ids[1].product_id.id,
            product_customerinfos[1].product_id.id)
        self.assertEqual(
            wizard.line_ids[1].sequence, product_customerinfos[1].sequence)
        self.assertEqual(
            wizard.line_ids[1].product_name,
            product_customerinfos[1].product_name)
        self.assertEqual(
            wizard.line_ids[1].product_code,
            product_customerinfos[1].product_code)
        self.assertEqual(
            wizard.line_ids[1].min_qty, product_customerinfos[1].min_qty)
        self.assertEqual(
            wizard.line_ids[1].price, product_customerinfos[1].price)
        self.assertEqual(
            wizard.line_ids[1].delay, product_customerinfos[1].delay)
        self.assertEqual(
            wizard.line_ids[1].date_start, product_customerinfos[1].date_start)
        self.assertEqual(
            wizard.line_ids[1].date_end, product_customerinfos[1].date_end)
        result = wizard.button_accept()
        len_product_customerinfo2 = self.env['product.customerinfo'].search([])
        self.assertEqual(
            len(len_product_customerinfo2), len(len_product_customerinfo1) + 2)
        self.assertEqual(result['name'], 'Product customer info created')
        product_customerinfos = self.env['product.customerinfo'].search([
            ('name', '=', self.partner_2.id),
            ('product_tmpl_id', 'in', [
                self.product_1.product_tmpl_id.id,
                self.product_2.product_tmpl_id.id]),
        ])
        self.assertEqual(len(product_customerinfos), 2)

    def test_copy_duplicated_customerinfo(self):
        product_customerinfo_1 = self.env['product.customerinfo'].create({
            'name': self.partner_1.id,
            'product_id': self.product_1.id,
            'product_tmpl_id': self.product_1.product_tmpl_id.id,
            'sequence': 1,
            'product_name': self.product_1.name,
            'product_code': self.product_1.default_code,
            'min_qty': 5,
            'delay': 2,
            'price': 8,
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(months=1),
        })
        self.env['product.customerinfo'].create({
            'name': self.partner_2.id,
            'product_id': self.product_2.id,
            'product_tmpl_id': self.product_1.product_tmpl_id.id,
            'sequence': 2,
            'product_name': self.product_1.name,
            'product_code': self.product_1.default_code,
            'min_qty': 5,
            'delay': 1,
            'price': 8,
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(months=1),
        })
        product_customerinfos_1 = self.env['product.customerinfo'].search([])
        wizard = self.env['product.customerinfo.copy'].with_context(
            active_ids=product_customerinfo_1.id).create({
                'partner_id': self.partner_2.id,
            })
        self.assertEqual(wizard.partner_id.id, self.partner_2.id)
        self.assertEqual(len(wizard.line_ids), 1)
        result = wizard.button_accept()
        self.assertEqual(result['name'], 'Product customer info created')
        product_customerinfos_2 = self.env['product.customerinfo'].search([])
        self.assertEqual(
            len(product_customerinfos_1), len(product_customerinfos_2))
