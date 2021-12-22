###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo import _
from odoo.tests.common import TransactionCase


class TestImportTemplatePartner(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['res.partner.category'].create({
            'name': 'Partner categ 1',
        })
        self.env['res.partner.category'].create({
            'name': 'Partner categ 2',
        })
        partner_id_field = self.env['ir.model.fields'].search([
            ('name', '=', 'partner_id'),
        ], limit=1)
        self.env['sale.invoice.group.method'].create({
            'name': 'By partner',
            'criteria_fields_ids': [(6, 0, [partner_id_field.id])],
        })
        self.env['account.payment.mode'].create({
            'name': 'Payment mode customer',
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'payment_type': 'inbound',
            'bank_account_link': 'variable',
        })
        self.env['account.payment.mode'].create({
            'name': 'Payment mode supplier',
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_out').id,
            'payment_type': 'outbound',
            'bank_account_link': 'variable',
        })
        self.env['product.pricelist.purchase'].create({
            'name': 'Pricelist purchase',
        })
        self.env['account.fiscal.position'].create({
            'name': 'Fiscal position test',
        })
        self.env['credit.control.policy'].create({
            'name': 'Credit control policy test',
            'do_nothing': True,
        })
        self.env['sale.commission'].create({
            'name': 'Test commission 10%',
            'fix_qty': 10,
        })
        self.commission = self.env['sale.commission'].create({
            'name': 'Commission test 3%',
            'fix_qty': 3,
        })
        self.env['res.partner'].create({
            'name': 'Agent test 1',
            'agent': True,
            'agent_type': 'agent',
            'email': 'agent@agent.com',
            'commission': self.commission.id,
            'settlement': 'monthly',
        })
        self.env['res.partner'].create({
            'name': 'Agent test 2',
            'agent': True,
            'agent_type': 'agent',
            'email': 'agent@mail.com',
            'commission': self.commission.id,
            'settlement': 'monthly',
        })

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def get_file_name(self, fname):
        return fname.split('/')[-1:][0]

    def test_import_create_base_ok(self):
        fname = self.get_sample('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '3: Contact Customer 1 not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: Contact Customer 1 not found.'), wizard.line_ids[1].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 0)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        agent_1 = self.env['res.partner'].search([
            ('name', '=', 'Agent 1'),
        ])
        self.assertEquals(len(agent_1), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertFalse(partners_1.invoice_group_method_id.exists())
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 1)
        self.assertEquals(partners_2.company_type, 'company')
        self.assertEquals(partners_2.comercial, '')
        self.assertFalse(partners_2.vat)
        self.assertFalse(partners_2.parent_id.exists())
        self.assertEquals(partners_2.type, False)
        self.assertEquals(partners_2.street, 'Moon, 2')
        self.assertEquals(partners_2.street2, '')
        self.assertEquals(partners_2.city, 'Brussels')
        self.assertEquals(partners_2.city_id.name, 'Brussels')
        self.assertFalse(partners_2.state_id)
        self.assertEquals(partners_2.zip_id.name, '1000')
        self.assertEquals(partners_2.country_id.name, 'Belgium')
        self.assertEquals(partners_2.phone, '')
        self.assertEquals(partners_2.mobile, '')
        self.assertEquals(partners_2.email, '')
        self.assertEquals(partners_2.website, '')
        self.assertEquals(len(partners_2.category_id), 0)
        self.assertEquals(partners_2.comment, '')
        self.assertEquals(partners_2.customer, True)
        self.assertEquals(partners_2.supplier, False)
        self.assertEquals(partners_2.agent, False)
        self.assertEquals(partners_2.agent_type, 'agent')
        self.assertEquals(partners_2.settlement, 'monthly')
        self.assertFalse(partners_2.user_id)
        self.assertFalse(partners_2.invoice_group_method_id.exists())
        self.assertEquals(partners_2.ref, '')
        agent_1 = self.env['res.partner'].search([
            ('name', '=', 'Agent 1'),
        ])
        self.assertEquals(len(agent_1), 1)
        self.assertEquals(agent_1.company_type, 'company')
        self.assertEquals(agent_1.comercial, '')
        self.assertFalse(agent_1.vat)
        self.assertFalse(agent_1.parent_id.exists())
        self.assertEquals(agent_1.type, False)
        self.assertEquals(agent_1.street, 'Moon, 2')
        self.assertEquals(agent_1.street2, '')
        self.assertEquals(agent_1.city, 'Brussels')
        self.assertEquals(agent_1.city_id.name, 'Brussels')
        self.assertFalse(agent_1.state_id)
        self.assertEquals(agent_1.zip_id.name, '1000')
        self.assertEquals(agent_1.country_id.name, 'Belgium')
        self.assertEquals(agent_1.phone, '')
        self.assertEquals(agent_1.mobile, '')
        self.assertEquals(agent_1.email, '')
        self.assertEquals(agent_1.website, '')
        self.assertEquals(len(agent_1.category_id), 0)
        self.assertEquals(agent_1.comment, '')
        self.assertEquals(agent_1.customer, False)
        self.assertEquals(agent_1.supplier, False)
        self.assertEquals(agent_1.agent, True)
        self.assertEquals(agent_1.agent_type, 'agent')
        self.assertEquals(agent_1.settlement, 'annual')
        self.assertFalse(agent_1.user_id)
        self.assertEquals(agent_1.ref, '')

    def test_import_write_base_ok(self):
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        fname = self.get_sample('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        self.assertEquals(len(partners_2), 0)
        agent_1 = self.env['res.partner'].search([
            ('name', '=', 'Agent 1'),
        ])
        self.assertEquals(len(agent_1), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertFalse(partners_1.invoice_group_method_id.exists())
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 1)
        self.assertEquals(partners_2.company_type, 'company')
        self.assertEquals(partners_2.comercial, '')
        self.assertFalse(partners_2.vat)
        self.assertFalse(partners_2.parent_id.exists())
        self.assertEquals(partners_2.type, False)
        self.assertEquals(partners_2.street, 'Moon, 2')
        self.assertEquals(partners_2.street2, '')
        self.assertEquals(partners_2.city, 'Brussels')
        self.assertEquals(partners_2.city_id.name, 'Brussels')
        self.assertFalse(partners_2.state_id)
        self.assertEquals(partners_2.zip_id.name, '1000')
        self.assertEquals(partners_2.country_id.name, 'Belgium')
        self.assertEquals(partners_2.phone, '')
        self.assertEquals(partners_2.mobile, '')
        self.assertEquals(partners_2.email, '')
        self.assertEquals(partners_2.website, '')
        self.assertEquals(len(partners_2.category_id), 0)
        self.assertEquals(partners_2.comment, '')
        self.assertEquals(partners_2.customer, True)
        self.assertEquals(partners_2.supplier, False)
        self.assertEquals(partners_2.agent, False)
        self.assertEquals(partners_2.agent_type, 'agent')
        self.assertEquals(partners_2.settlement, 'monthly')
        self.assertFalse(partners_2.user_id)
        self.assertFalse(partners_2.invoice_group_method_id.exists())
        self.assertEquals(partners_2.ref, '')
        agent_1 = self.env['res.partner'].search([
            ('name', '=', 'Agent 1'),
        ])
        self.assertEquals(len(agent_1), 1)
        self.assertEquals(agent_1.company_type, 'company')
        self.assertEquals(agent_1.comercial, '')
        self.assertFalse(agent_1.vat)
        self.assertFalse(agent_1.parent_id.exists())
        self.assertEquals(agent_1.type, False)
        self.assertEquals(agent_1.street, 'Moon, 2')
        self.assertEquals(agent_1.street2, '')
        self.assertEquals(agent_1.city, 'Brussels')
        self.assertEquals(agent_1.city_id.name, 'Brussels')
        self.assertFalse(agent_1.state_id)
        self.assertEquals(agent_1.zip_id.name, '1000')
        self.assertEquals(agent_1.country_id.name, 'Belgium')
        self.assertEquals(agent_1.phone, '')
        self.assertEquals(agent_1.mobile, '')
        self.assertEquals(agent_1.email, '')
        self.assertEquals(agent_1.website, '')
        self.assertEquals(len(agent_1.category_id), 0)
        self.assertEquals(agent_1.comment, '')
        self.assertEquals(agent_1.customer, False)
        self.assertEquals(agent_1.supplier, False)
        self.assertEquals(agent_1.agent, True)
        self.assertEquals(agent_1.agent_type, 'agent')
        self.assertEquals(agent_1.settlement, 'annual')
        self.assertFalse(agent_1.user_id)
        self.assertEquals(agent_1.ref, '')

    def test_import_create_with_category_id(self):
        fname = self.get_sample('sample_with_category_id.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 5)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '3: Contact Customer 1 not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: Contact Customer 1 not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '5: Partner category (tag) Partner categ 3 not found.'),
            wizard.line_ids[2].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 0)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Partner category (tag) Partner categ 3 not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 2)
        self.assertEquals(partners_1.category_id[0].name, 'Partner categ 1')
        self.assertEquals(partners_1.category_id[1].name, 'Partner categ 2')
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertFalse(partners_1.invoice_group_method_id.exists())
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 1)
        self.assertEquals(partners_3.category_id.name, 'Partner categ 1')
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertFalse(partners_3.invoice_group_method_id.exists())
        self.assertEquals(partners_3.ref, '')

    def test_import_write_with_category_id(self):
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        fname = self.get_sample('sample_with_category_id.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Partner category (tag) Partner categ 3 not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Partner category (tag) Partner categ 3 not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 2)
        self.assertEquals(partners_1.category_id[0].name, 'Partner categ 1')
        self.assertEquals(partners_1.category_id[1].name, 'Partner categ 2')
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertFalse(partners_1.invoice_group_method_id.exists())
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 1)
        self.assertEquals(partners_3.category_id.name, 'Partner categ 1')
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertFalse(partners_3.invoice_group_method_id.exists())
        self.assertEquals(partners_3.ref, '')

    def test_import_create_with_invoice_group_method_id(self):
        fname = self.get_sample('sample_with_invoice_group_method_id.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 5)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '3: Contact Customer 1 not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: Contact Customer 1 not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '5: Sale Invoice Group Method By sale date not found.'),
            wizard.line_ids[2].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 0)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Sale Invoice Group Method By sale date not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(len(partners_1.invoice_group_method_id), 1)
        self.assertEquals(
            partners_1.invoice_group_method_id.name, 'By partner')
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertFalse(partners_3.invoice_group_method_id.exists())
        self.assertEquals(partners_3.ref, '')

    def test_import_write_with_invoice_group_method_id(self):
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        fname = self.get_sample('sample_with_invoice_group_method_id.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Sale Invoice Group Method By sale date not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Sale Invoice Group Method By sale date not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(len(partners_1.invoice_group_method_id), 1)
        self.assertEquals(
            partners_1.invoice_group_method_id.name, 'By partner')
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertFalse(partners_3.invoice_group_method_id.exists())
        self.assertEquals(partners_3.ref, '')

    def test_import_create_with_payment_term_id(self):
        fname = self.get_sample('sample_with_payment_term_id.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 4)
        self.assertIn(_(
            '3: Contact Customer 1 not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: Contact Customer 1 not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '5: Payment Terms Other day not found.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '5: Payment Terms Or another day not found.'),
            wizard.line_ids[3].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 0)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '5: Payment Terms Other day not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '5: Payment Terms Or another day not found.'),
            wizard.line_ids[1].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(len(partners_1.property_payment_term_id), 1)
        self.assertEquals(
            partners_1.property_payment_term_id.name, 'Immediate Payment')
        self.assertEquals(len(partners_1.property_supplier_payment_term_id), 1)
        self.assertEquals(
            partners_1.property_supplier_payment_term_id.name, '15 Days')
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertFalse(partners_3.property_payment_term_id)
        self.assertFalse(partners_3.property_supplier_payment_term_id)
        self.assertEquals(partners_3.ref, '')

    def test_import_write_with_payment_term_id(self):
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        fname = self.get_sample('sample_with_payment_term_id.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '5: Payment Terms Other day not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '5: Payment Terms Or another day not found.'),
            wizard.line_ids[1].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '5: Payment Terms Other day not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '5: Payment Terms Or another day not found.'),
            wizard.line_ids[1].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(len(partners_1.property_payment_term_id), 1)
        self.assertEquals(
            partners_1.property_payment_term_id.name, 'Immediate Payment')
        self.assertEquals(len(partners_1.property_supplier_payment_term_id), 1)
        self.assertEquals(
            partners_1.property_supplier_payment_term_id.name, '15 Days')
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertFalse(partners_3.property_payment_term_id)
        self.assertFalse(partners_3.property_supplier_payment_term_id)
        self.assertEquals(partners_3.ref, '')

    def test_import_create_with_payment_mode_id(self):
        fname = self.get_sample('sample_with_payment_mode_id.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 4)
        self.assertIn(_(
            '3: Contact Customer 1 not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: Contact Customer 1 not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '5: Payment Modes Other payment mode customer not found.'),
            wizard.line_ids[2].name)
        self.assertIn(_(
            '5: Payment Modes Other payment mode supplier not found.'),
            wizard.line_ids[3].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 0)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '5: Payment Modes Other payment mode customer not found.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '5: Payment Modes Other payment mode supplier not found.'),
            wizard.line_ids[1].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(
            partners_1.customer_payment_mode_id.name, 'Payment mode customer')
        self.assertEquals(
            partners_1.supplier_payment_mode_id.name, 'Payment mode supplier')
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertFalse(partners_3.customer_payment_mode_id.exists())
        self.assertFalse(partners_3.supplier_payment_mode_id.exists())
        self.assertEquals(partners_3.ref, '')

    def test_import_write_with_payment_mode_id(self):
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        fname = self.get_sample('sample_with_payment_mode_id.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '5: Payment Modes Other payment mode customer not found.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '5: Payment Modes Other payment mode supplier not found.'),
            wizard.line_ids[1].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '5: Payment Modes Other payment mode customer not found.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '5: Payment Modes Other payment mode supplier not found.'),
            wizard.line_ids[1].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(
            partners_1.customer_payment_mode_id.name, 'Payment mode customer')
        self.assertEquals(
            partners_1.supplier_payment_mode_id.name, 'Payment mode supplier')
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertFalse(partners_3.customer_payment_mode_id.exists())
        self.assertFalse(partners_3.supplier_payment_mode_id.exists())
        self.assertEquals(partners_3.ref, '')

    def test_import_create_with_discount(self):
        fname = self.get_sample('sample_with_discount.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '3: Contact Customer 1 not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: Contact Customer 1 not found.'), wizard.line_ids[1].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 0)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(partners_1.default_supplierinfo_discount, 10.0)
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 1)
        self.assertEquals(partners_2.company_type, 'company')
        self.assertEquals(partners_2.comercial, '')
        self.assertFalse(partners_2.vat)
        self.assertFalse(partners_2.parent_id.exists())
        self.assertEquals(partners_2.type, False)
        self.assertEquals(partners_2.street, 'Moon, 2')
        self.assertEquals(partners_2.street2, '')
        self.assertEquals(partners_2.city, 'Brussels')
        self.assertEquals(partners_2.city_id.name, 'Brussels')
        self.assertFalse(partners_2.state_id)
        self.assertEquals(partners_2.zip_id.name, '1000')
        self.assertEquals(partners_2.country_id.name, 'Belgium')
        self.assertEquals(partners_2.phone, '')
        self.assertEquals(partners_2.mobile, '')
        self.assertEquals(partners_2.email, '')
        self.assertEquals(partners_2.website, '')
        self.assertEquals(len(partners_2.category_id), 0)
        self.assertEquals(partners_2.comment, '')
        self.assertEquals(partners_2.customer, True)
        self.assertEquals(partners_2.supplier, False)
        self.assertEquals(partners_2.agent, False)
        self.assertEquals(partners_2.agent_type, 'agent')
        self.assertEquals(partners_2.settlement, 'monthly')
        self.assertFalse(partners_2.user_id)
        self.assertEquals(partners_2.default_supplierinfo_discount, -5)
        self.assertEquals(partners_2.ref, '')
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertEquals(partners_3.default_supplierinfo_discount, 0)
        self.assertEquals(partners_3.ref, '')

    def test_import_write_with_discount(self):
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        fname = self.get_sample('sample_with_discount.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(partners_1.default_supplierinfo_discount, 10.0)
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 1)
        self.assertEquals(partners_2.company_type, 'company')
        self.assertEquals(partners_2.comercial, '')
        self.assertFalse(partners_2.vat)
        self.assertFalse(partners_2.parent_id.exists())
        self.assertEquals(partners_2.type, False)
        self.assertEquals(partners_2.street, 'Moon, 2')
        self.assertEquals(partners_2.street2, '')
        self.assertEquals(partners_2.city, 'Brussels')
        self.assertEquals(partners_2.city_id.name, 'Brussels')
        self.assertFalse(partners_2.state_id)
        self.assertEquals(partners_2.zip_id.name, '1000')
        self.assertEquals(partners_2.country_id.name, 'Belgium')
        self.assertEquals(partners_2.phone, '')
        self.assertEquals(partners_2.mobile, '')
        self.assertEquals(partners_2.email, '')
        self.assertEquals(partners_2.website, '')
        self.assertEquals(len(partners_2.category_id), 0)
        self.assertEquals(partners_2.comment, '')
        self.assertEquals(partners_2.customer, True)
        self.assertEquals(partners_2.supplier, False)
        self.assertEquals(partners_2.agent, False)
        self.assertEquals(partners_2.agent_type, 'agent')
        self.assertEquals(partners_2.settlement, 'monthly')
        self.assertFalse(partners_2.user_id)
        self.assertEquals(partners_2.default_supplierinfo_discount, -5)
        self.assertEquals(partners_2.ref, '')
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertEquals(partners_3.default_supplierinfo_discount, 0)
        self.assertEquals(partners_3.ref, '')

    def test_import_create_with_product_pricelist(self):
        fname = self.get_sample('sample_with_product_pricelist.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 4)
        self.assertIn(_(
            '3: Contact Customer 1 not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: Contact Customer 1 not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '5: Pricelist Other pricelist not found.'),
            wizard.line_ids[2].name)
        self.assertIn(_(
            '5: product.pricelist.purchase Other pricelist purchase not '
            'found.'), wizard.line_ids[3].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 0)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '5: Pricelist Other pricelist not found.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '5: product.pricelist.purchase Other pricelist purchase not '
            'found.'), wizard.line_ids[1].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(
            partners_1.property_product_pricelist.name, 'Public Pricelist')
        self.assertEquals(
            partners_1.supplier_pricelist_id.name, 'Pricelist purchase')
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertEquals(
            partners_1.property_product_pricelist.name, 'Public Pricelist')
        self.assertEquals(
            partners_1.supplier_pricelist_id.name, 'Pricelist purchase')
        self.assertEquals(partners_1.ref, 'Ref 1')
        self.assertEquals(partners_3.ref, '')

    def test_import_write_with_product_pricelist(self):
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        fname = self.get_sample('sample_with_product_pricelist.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '5: Pricelist Other pricelist not found.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '5: product.pricelist.purchase Other pricelist purchase not '
            'found.'), wizard.line_ids[1].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '5: Pricelist Other pricelist not found.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '5: product.pricelist.purchase Other pricelist purchase not '
            'found.'), wizard.line_ids[1].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(
            partners_1.property_product_pricelist.name, 'Public Pricelist')
        self.assertEquals(
            partners_1.supplier_pricelist_id.name, 'Pricelist purchase')
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertEquals(
            partners_1.property_product_pricelist.name, 'Public Pricelist')
        self.assertEquals(
            partners_1.supplier_pricelist_id.name, 'Pricelist purchase')
        self.assertEquals(partners_1.ref, 'Ref 1')
        self.assertEquals(partners_3.ref, '')

    def test_import_create_with_account_position_id(self):
        fname = self.get_sample('sample_with_account_position_id.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 5)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '3: Contact Customer 1 not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: Contact Customer 1 not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '5: Fiscal Position Other fiscal position not found.'),
            wizard.line_ids[2].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 0)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Fiscal Position Other fiscal position not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(partners_1.ref, 'Ref 1')
        self.assertEquals(
            partners_1.property_account_position_id.name,
            'Fiscal position test')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertEquals(partners_3.ref, '')
        self.assertFalse(partners_3.property_account_position_id.exists())

    def test_import_write_with_account_position_id(self):
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        fname = self.get_sample('sample_with_account_position_id.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Fiscal Position Other fiscal position not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Fiscal Position Other fiscal position not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(partners_1.ref, 'Ref 1')
        self.assertEquals(
            partners_1.property_account_position_id.name,
            'Fiscal position test')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertEquals(partners_3.ref, '')
        self.assertFalse(partners_3.property_account_position_id.exists())

    def test_import_create_with_credit_control(self):
        fname = self.get_sample('sample_with_credit_control.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 5)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '3: Contact Customer 1 not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: Contact Customer 1 not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '5: Define a reminder policy Other control policy not found.'),
            wizard.line_ids[2].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 0)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Define a reminder policy Other control policy not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(partners_1.ref, 'Ref 1')
        self.assertEquals(
            partners_1.credit_policy_id.name, 'Credit control policy test')
        self.assertEquals(
            partners_1.payment_responsible_id.name, 'Mitchell Admin')
        self.assertEquals(partners_1.payment_note, 'Payment note test')
        self.assertEquals(partners_1.payment_next_action, 'Next action test')
        self.assertEquals(
            partners_1.payment_next_action_date.strftime(
                '%Y-%m-%d'), '2021-01-01')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertEquals(partners_3.ref, '')
        self.assertEquals(
            partners_1.credit_policy_id.name, 'Credit control policy test')
        self.assertEquals(
            partners_1.payment_responsible_id.name, 'Mitchell Admin')
        self.assertEquals(partners_1.payment_note, 'Payment note test')
        self.assertEquals(partners_1.payment_next_action, 'Next action test')
        self.assertEquals(
            partners_1.payment_next_action_date.strftime(
                '%Y-%m-%d'), '2021-01-01')

    def test_import_write_with_credit_control(self):
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        fname = self.get_sample('sample_with_credit_control.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Define a reminder policy Other control policy not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Define a reminder policy Other control policy not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(partners_1.ref, 'Ref 1')
        self.assertEquals(
            partners_1.credit_policy_id.name, 'Credit control policy test')
        self.assertEquals(
            partners_1.payment_responsible_id.name, 'Mitchell Admin')
        self.assertEquals(partners_1.payment_note, 'Payment note test')
        self.assertEquals(partners_1.payment_next_action, 'Next action test')
        self.assertEquals(
            partners_1.payment_next_action_date.strftime(
                '%Y-%m-%d'), '2021-01-01')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertEquals(partners_3.ref, '')
        self.assertEquals(
            partners_1.credit_policy_id.name, 'Credit control policy test')
        self.assertEquals(
            partners_1.payment_responsible_id.name, 'Mitchell Admin')
        self.assertEquals(partners_1.payment_note, 'Payment note test')
        self.assertEquals(partners_1.payment_next_action, 'Next action test')
        self.assertEquals(
            partners_1.payment_next_action_date.strftime(
                '%Y-%m-%d'), '2021-01-01')

    def test_import_create_with_commission(self):
        fname = self.get_sample('sample_with_commission.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 5)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '3: Contact Customer 1 not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: Contact Customer 1 not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '5: Commission in sales Other commission not found.'),
            wizard.line_ids[2].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 0)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Commission in sales Other commission not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.commission.name, 'Test commission 10%')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertFalse(partners_3.commission)
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertEquals(partners_3.ref, '')

    def test_import_write_with_commission(self):
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        fname = self.get_sample('sample_with_commission.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Commission in sales Other commission not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '5: Commission in sales Other commission not found.'),
            wizard.line_ids[0].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        self.assertFalse(partners_1.parent_id.exists())
        self.assertEquals(partners_1.type, False)
        self.assertEquals(partners_1.street, 'Real, 33')
        self.assertEquals(partners_1.street2, 'Building 4')
        self.assertEquals(partners_1.city, 'Armilla')
        self.assertFalse(partners_1.city_id.exists())
        self.assertEquals(partners_1.state_id.name, 'Granada')
        self.assertFalse(partners_1.zip_id.exists())
        self.assertEquals(partners_1.country_id.name, 'Spain')
        self.assertEquals(partners_1.phone, '958958958')
        self.assertEquals(partners_1.mobile, '666555666')
        self.assertEquals(partners_1.email, 'customer@test.es')
        self.assertEquals(partners_1.website, 'http://www.customer.es')
        self.assertEquals(len(partners_1.category_id), 0)
        self.assertEquals(partners_1.comment, 'Notes from tests.')
        self.assertEquals(partners_1.customer, True)
        self.assertEquals(partners_1.supplier, False)
        self.assertEquals(partners_1.agent, False)
        self.assertEquals(partners_1.agent_type, 'agent')
        self.assertEquals(partners_1.commission.name, 'Test commission 10%')
        self.assertEquals(partners_1.settlement, 'monthly')
        self.assertEquals(partners_1.user_id.name, 'Mitchell Admin')
        self.assertEquals(partners_1.ref, 'Ref 1')
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_1), 1)
        self.assertEquals(partners_1_1.type, 'contact')
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
            ('parent_id', '=', partners_1.id),
        ])
        self.assertEquals(len(partners_1_2), 1)
        self.assertEquals(partners_1_2.type, 'invoice')
        self.assertEquals(partners_1_2.street, 'Sun, 100')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_3), 1)
        self.assertEquals(partners_3.company_type, 'company')
        self.assertEquals(partners_3.comercial, '')
        self.assertFalse(partners_3.vat)
        self.assertFalse(partners_3.parent_id.exists())
        self.assertEquals(partners_3.type, False)
        self.assertEquals(partners_3.street, 'Moon, 3')
        self.assertEquals(partners_3.street2, '')
        self.assertEquals(partners_3.city, 'Brussels')
        self.assertEquals(partners_3.city_id.name, 'Brussels')
        self.assertFalse(partners_3.state_id)
        self.assertEquals(partners_3.zip_id.name, '1000')
        self.assertEquals(partners_3.country_id.name, 'Belgium')
        self.assertEquals(partners_3.phone, '')
        self.assertEquals(partners_3.mobile, '')
        self.assertEquals(partners_3.email, '')
        self.assertEquals(partners_3.website, '')
        self.assertEquals(len(partners_3.category_id), 0)
        self.assertEquals(partners_3.comment, '')
        self.assertEquals(partners_3.customer, True)
        self.assertEquals(partners_3.supplier, False)
        self.assertEquals(partners_3.agent, False)
        self.assertEquals(partners_3.agent_type, 'agent')
        self.assertFalse(partners_3.commission)
        self.assertEquals(partners_3.settlement, 'monthly')
        self.assertFalse(partners_3.user_id)
        self.assertEquals(partners_3.ref, '')

    def test_import_create_required_fields(self):
        fname = self.get_sample('sample_required_fields.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 7)
        self.assertEquals(len(wizard.line_ids), 15)
        self.assertEquals(wizard.total_warn, 4)
        self.assertEquals(wizard.total_error, 11)
        self.assertIn(_(
            '3: Contact Customer 1 not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '3: The \'company_type\' field is required.'),
            wizard.line_ids[2].name)
        self.assertIn(_(
            '4: Contact Customer 1 not found.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '4: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[4].name)
        self.assertIn(_(
            '4: The \'name\' field is required.'), wizard.line_ids[5].name)
        self.assertIn(_(
            '4: The \'company_type\' field is required.'),
            wizard.line_ids[6].name)
        self.assertIn(_(
            '5: Contact Customer 1 not found.'), wizard.line_ids[7].name)
        self.assertIn(_(
            '6: The \'name\' field is required.'), wizard.line_ids[8].name)
        self.assertIn(_(
            '7: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[9].name)
        self.assertIn(_(
            '7: The \'company_type\' field is required.'),
            wizard.line_ids[10].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 0)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', ''),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Contact without parent created'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', ''),
        ])
        self.assertEquals(len(partners_3), 0)
        partners_4 = self.env['res.partner'].search([
            ('name', '=', 'Customer 4'),
        ])
        self.assertEquals(len(partners_4), 0)
        agent_1 = self.env['res.partner'].search([
            ('name', '=', 'Agent 1'),
        ])
        self.assertEquals(len(agent_1), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 7)
        self.assertEquals(len(wizard.line_ids), 12)
        self.assertEquals(wizard.total_warn, 4)
        self.assertEquals(wizard.total_error, 8)
        self.assertIn(_(
            '3: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'company_type\' field is required.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '4: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '4: The \'name\' field is required.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '4: The \'company_type\' field is required.'),
            wizard.line_ids[4].name)
        self.assertIn(_(
            '6: The \'name\' field is required.'), wizard.line_ids[5].name)
        self.assertIn(_(
            '7: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[6].name)
        self.assertIn(_(
            '7: The \'company_type\' field is required.'),
            wizard.line_ids[7].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', ''),
            ('type', '=', 'invoice'),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Contact without parent created'),
        ])
        self.assertEquals(len(partners_2), 1)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', ''),
            ('street2', '=', 'Moon, 2'),
        ])
        self.assertEquals(len(partners_3), 0)
        partners_4 = self.env['res.partner'].search([
            ('name', '=', 'Customer 4'),
        ])
        self.assertEquals(len(partners_4), 0)
        agent_1 = self.env['res.partner'].search([
            ('name', '=', 'Agent 1'),
        ])
        self.assertEquals(len(agent_1), 1)
        self.assertEquals(agent_1.company_type, 'company')
        self.assertEquals(agent_1.comercial, '')
        self.assertFalse(agent_1.vat)
        self.assertFalse(agent_1.parent_id.exists())
        self.assertEquals(agent_1.type, False)
        self.assertEquals(agent_1.street, 'Moon, 4')
        self.assertEquals(agent_1.street2, '')
        self.assertEquals(agent_1.city, 'Brussels')
        self.assertEquals(agent_1.city_id.name, 'Brussels')
        self.assertFalse(agent_1.state_id)
        self.assertEquals(agent_1.zip_id.name, '1000')
        self.assertEquals(agent_1.country_id.name, 'Belgium')
        self.assertEquals(agent_1.phone, '')
        self.assertEquals(agent_1.mobile, '')
        self.assertEquals(agent_1.email, '')
        self.assertEquals(agent_1.website, '')
        self.assertEquals(len(agent_1.category_id), 0)
        self.assertEquals(agent_1.comment, '')
        self.assertEquals(agent_1.customer, False)
        self.assertEquals(agent_1.supplier, False)
        self.assertEquals(agent_1.agent, True)
        self.assertEquals(agent_1.agent_type, 'agent')
        self.assertEquals(agent_1.settlement, 'annual')
        self.assertFalse(agent_1.user_id)
        self.assertEquals(agent_1.ref, '')

    def test_import_write_required_fields(self):
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        fname = self.get_sample('sample_required_fields.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 7)
        self.assertEquals(len(wizard.line_ids), 12)
        self.assertEquals(wizard.total_warn, 4)
        self.assertEquals(wizard.total_error, 8)
        self.assertIn(_(
            '3: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'company_type\' field is required.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '4: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '4: The \'name\' field is required.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '4: The \'company_type\' field is required.'),
            wizard.line_ids[4].name)
        self.assertIn(_(
            '6: The \'name\' field is required.'), wizard.line_ids[5].name)
        self.assertIn(_(
            '7: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[6].name)
        self.assertIn(_(
            '7: The \'company_type\' field is required.'),
            wizard.line_ids[7].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', ''),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Contact without parent created'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', ''),
        ])
        self.assertEquals(len(partners_3), 0)
        partners_4 = self.env['res.partner'].search([
            ('name', '=', 'Customer 4'),
        ])
        self.assertEquals(len(partners_4), 0)
        agent_1 = self.env['res.partner'].search([
            ('name', '=', 'Agent 1'),
        ])
        self.assertEquals(len(agent_1), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 7)
        self.assertEquals(len(wizard.line_ids), 12)
        self.assertEquals(wizard.total_warn, 4)
        self.assertEquals(wizard.total_error, 8)
        self.assertIn(_(
            '3: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'company_type\' field is required.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '4: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '4: The \'name\' field is required.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '4: The \'company_type\' field is required.'),
            wizard.line_ids[4].name)
        self.assertIn(_(
            '6: The \'name\' field is required.'), wizard.line_ids[5].name)
        self.assertIn(_(
            '7: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[6].name)
        self.assertIn(_(
            '7: The \'company_type\' field is required.'),
            wizard.line_ids[7].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_1_2 = self.env['res.partner'].search([
            ('name', '=', ''),
            ('type', '=', 'invoice'),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Contact without parent created'),
        ])
        self.assertEquals(len(partners_2), 1)
        self.assertEquals(partners_2.company_type, 'person')
        self.assertEquals(partners_2.comercial, 'Customer Engine')
        self.assertFalse(partners_2.vat, '')
        self.assertEquals(partners_2.parent_id, partners_1)
        self.assertEquals(partners_2.type, 'invoice')
        self.assertEquals(partners_2.street, 'Sun, 33')
        self.assertEquals(partners_2.street2, '')
        self.assertEquals(partners_2.city, '')
        self.assertFalse(partners_2.city_id)
        self.assertFalse(partners_2.state_id)
        self.assertFalse(partners_2.zip_id)
        self.assertFalse(partners_2.country_id)
        self.assertEquals(partners_2.phone, '')
        self.assertEquals(partners_2.mobile, '')
        self.assertEquals(partners_2.email, '')
        self.assertEquals(partners_2.website, '')
        self.assertEquals(len(partners_2.category_id), 0)
        self.assertEquals(partners_2.comment, '')
        self.assertEquals(partners_2.customer, True)
        self.assertEquals(partners_2.supplier, False)
        self.assertEquals(partners_2.agent, False)
        self.assertEquals(partners_2.agent_type, 'agent')
        self.assertEquals(partners_2.settlement, 'monthly')
        self.assertFalse(partners_2.user_id)
        self.assertEquals(partners_2.ref, '')
        partners_3 = self.env['res.partner'].search([
            ('name', '=', ''),
            ('street2', '=', 'Moon, 2'),
        ])
        self.assertEquals(len(partners_3), 0)
        partners_4 = self.env['res.partner'].search([
            ('name', '=', 'Customer 4'),
        ])
        self.assertEquals(len(partners_4), 0)
        agent_1 = self.env['res.partner'].search([
            ('name', '=', 'Agent 1'),
        ])
        self.assertEquals(len(agent_1), 1)
        self.assertEquals(agent_1.company_type, 'company')
        self.assertEquals(agent_1.comercial, '')
        self.assertFalse(agent_1.vat)
        self.assertFalse(agent_1.parent_id.exists())
        self.assertEquals(agent_1.type, False)
        self.assertEquals(agent_1.street, 'Moon, 4')
        self.assertEquals(agent_1.street2, '')
        self.assertEquals(agent_1.city, 'Brussels')
        self.assertEquals(agent_1.city_id.name, 'Brussels')
        self.assertFalse(agent_1.state_id)
        self.assertEquals(agent_1.zip_id.name, '1000')
        self.assertEquals(agent_1.country_id.name, 'Belgium')
        self.assertEquals(agent_1.phone, '')
        self.assertEquals(agent_1.mobile, '')
        self.assertEquals(agent_1.email, '')
        self.assertEquals(agent_1.website, '')
        self.assertEquals(len(agent_1.category_id), 0)
        self.assertEquals(agent_1.comment, '')
        self.assertEquals(agent_1.customer, False)
        self.assertEquals(agent_1.supplier, False)
        self.assertEquals(agent_1.agent, True)
        self.assertEquals(agent_1.agent_type, 'agent')
        self.assertEquals(agent_1.settlement, 'annual')
        self.assertFalse(agent_1.user_id)
        self.assertEquals(agent_1.ref, '')

    def test_import_create_wrong_values(self):
        fname = self.get_sample('sample_wrong_values.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 8)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 6)
        self.assertIn(_(
            '2: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: The \'company_type\' field is required.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '2: Partner category (tag) Partner categ 1,Partner categ 2 not '
            'found.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '3: Contact Customer 1 not found.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '3: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[4].name)
        self.assertIn(_(
            '3: The \'company_type\' field is required.'),
            wizard.line_ids[5].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 0)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        agent_1 = self.env['res.partner'].search([
            ('name', '=', 'Agent 1'),
        ])
        self.assertEquals(len(agent_1), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 8)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 6)
        self.assertIn(_(
            '2: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: The \'company_type\' field is required.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '2: Partner category (tag) Partner categ 1,Partner categ 2 not '
            'found.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '3: Contact Customer 1 not found.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '3: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[4].name)
        self.assertIn(_(
            '3: The \'company_type\' field is required.'),
            wizard.line_ids[5].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 0)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 1)
        self.assertEquals(partners_2.customer, True)
        self.assertEquals(partners_2.type, False)
        agent_1 = self.env['res.partner'].search([
            ('name', '=', 'Agent 1'),
        ])
        self.assertEquals(len(agent_1), 1)

    def test_import_write_wrong_values(self):
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        fname = self.get_sample('sample_wrong_values.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 7)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 5)
        self.assertIn(_(
            '2: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: The \'company_type\' field is required.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '2: Partner category (tag) Partner categ 1,Partner categ 2 not '
            'found.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '3: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '3: The \'company_type\' field is required.'),
            wizard.line_ids[4].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 0)
        agent_1 = self.env['res.partner'].search([
            ('name', '=', 'Agent 1'),
        ])
        self.assertEquals(len(agent_1), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 7)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 5)
        self.assertIn(_(
            '2: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: The \'company_type\' field is required.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '2: Partner category (tag) Partner categ 1,Partner categ 2 not '
            'found.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '3: Option \'False\' for \'company_type\' does not exist. You '
            'must choose a valid value.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '3: The \'company_type\' field is required.'),
            wizard.line_ids[4].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_1_1 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_1_1), 0)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_2), 1)
        self.assertEquals(partners_2.customer, True)
        self.assertEquals(partners_2.type, False)
        agent_1 = self.env['res.partner'].search([
            ('name', '=', 'Agent 1'),
        ])
        self.assertEquals(len(agent_1), 1)

    def test_import_partner_with_agent(self):
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        self.env['res.partner'].create({
            'name': 'Agent test 3',
            'agent': True,
            'agent_type': 'agent',
            'email': 'agent@hotmail.com',
            'commission': self.commission.id,
            'settlement': 'monthly',
        })
        self.env['res.partner'].create({
            'name': 'Agent test 3',
            'agent': True,
            'agent_type': 'agent',
            'email': 'agent3@mail.es',
            'commission': self.commission.id,
            'settlement': 'monthly',
        })
        fname = self.get_sample('sample_with_agent.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '6: Agent with name Agent X not found'), wizard.line_ids[0].name)
        self.assertIn(_(
            '7: Agents found with same name Agent test 3'),
            wizard.line_ids[1].name)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '6: Agent with name Agent X not found'), wizard.line_ids[0].name)
        self.assertIn(_(
            '7: Agents found with same name Agent test 3'),
            wizard.line_ids[1].name)
        partner_id = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partner_id), 1)
        self.assertEquals(len(partner_id.agents), 1)
        agent_1 = self.env['res.partner'].search([
            ('name', '=', 'Agent test 1'),
            ('agent', '=', True),
        ])
        self.assertEquals(partner_id.agents[0].id, agent_1.id)
        partner_id = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partner_id), 1)
        self.assertEquals(len(partner_id.agents), 2)
        agent_2 = self.env['res.partner'].search([
            ('name', '=', 'Agent test 2'),
            ('agent', '=', True),
        ])
        self.assertEquals(partner_id.agents[0].id, agent_1.id)
        self.assertEquals(partner_id.agents[1].id, agent_2.id)

    def test_import_partner_with_partner_group(self):
        name_group_2 = 'Test group 2'
        name_group_3 = 'Test group 3'
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        self.env['res.partner'].create({
            'name': 'Test group 1',
            'company_type': 'company',
            'ref': 'GROUP01',
        })
        self.env['res.partner'].create({
            'name': name_group_2,
            'company_type': 'company',
            'ref': 'GROUP02',
        })
        self.env['res.partner'].create({
            'name': name_group_2,
            'company_type': 'company',
            'ref': 'GROUP03',
        })
        fname = self.get_sample('sample_with_partner_group.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            _('3: More than one Contact found for %s' % name_group_2),
            wizard.line_ids[0].name)
        self.assertIn(
            _('4: Contact %s not found' % name_group_3),
            wizard.line_ids[1].name)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            _('3: More than one Contact found for %s' % name_group_2),
            wizard.line_ids[0].name)
        self.assertIn(
            _('4: Contact %s not found' % name_group_3),
            wizard.line_ids[1].name)
        partner_id = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partner_id), 1)
        self.assertEquals(len(partner_id.partner_group_id), 1)
        partner_group = self.env['res.partner'].search([
            ('name', '=', 'Test group 1'),
        ])
        self.assertEquals(len(partner_group), 1)
        self.assertEquals(partner_id.partner_group_id.id, partner_group.id)

    def test_import_partner_check_vat(self):
        self.env['res.partner'].create({
            'name': 'Customer 1',
            'company_type': 'company',
        })
        self.env['res.partner'].create({
            'name': 'Test group 1',
            'company_type': 'company',
            'ref': 'GROUP01',
        })
        self.env['res.partner'].create({
            'name': 'Test group 2',
            'company_type': 'company',
            'ref': 'GROUP02',
        })
        self.env['res.partner'].create({
            'name': 'Test group 2',
            'company_type': 'company',
            'ref': 'GROUP03',
        })
        fname = self.get_sample('sample_with_partner_group.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_partner.template_partner').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            _('5: VAT [ESA00000000] not valid for partner Customer 2'),
            wizard.line_ids[2].name)
        self.assertIn(
            _('6: VAT [ESA00000000] not valid for partner Customer 3'),
            wizard.line_ids[3].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
        ])
        self.assertEquals(len(partners_3), 0)
        partners_4 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_4), 0)
        partners_5 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_5), 0)
        partners_6 = self.env['res.partner'].search([
            ('name', '=', 'Customer 4'),
        ])
        self.assertEquals(len(partners_6), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            _('5: VAT [ESA00000000] not valid for partner Customer 2'),
            wizard.line_ids[2].name)
        self.assertIn(
            _('6: VAT [ESA00000000] not valid for partner Customer 3'),
            wizard.line_ids[3].name)
        partners_1 = self.env['res.partner'].search([
            ('name', '=', 'Customer 1'),
        ])
        self.assertEquals(len(partners_1), 1)
        self.assertEquals(partners_1.company_type, 'company')
        self.assertEquals(partners_1.comercial, 'Customer Engine')
        self.assertEquals(partners_1.vat, 'ESA00000000')
        partners_2 = self.env['res.partner'].search([
            ('name', '=', 'Contact 1'),
        ])
        self.assertEquals(len(partners_2), 0)
        partners_3 = self.env['res.partner'].search([
            ('name', '=', 'Invoice address'),
        ])
        self.assertEquals(len(partners_3), 0)
        partners_4 = self.env['res.partner'].search([
            ('name', '=', 'Customer 2'),
        ])
        self.assertEquals(len(partners_4), 1)
        self.assertFalse(partners_4.vat)
        partners_5 = self.env['res.partner'].search([
            ('name', '=', 'Customer 3'),
        ])
        self.assertEquals(len(partners_5), 1)
        self.assertFalse(partners_5.vat)
        partners_6 = self.env['res.partner'].search([
            ('name', '=', 'Customer 4'),
        ])
        self.assertEquals(len(partners_6), 1)
        self.assertEquals(partners_6.vat, 'BE0477472701')
