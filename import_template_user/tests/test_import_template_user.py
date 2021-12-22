###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo import _
from odoo.tests.common import TransactionCase


class TestImportTemplateUser(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_company = self.env['res.partner'].create({
            'name': 'Partner company',
            'is_company': True,
            'email': 'partner@example.org',
        })
        self.partner_contact_1 = self.env['res.partner'].create({
            'name': 'Partner contact',
            'parent_id': self.partner_company.id,
            'email': 'partner_contact@example.org',
        })
        self.partner_person = self.env['res.partner'].create({
            'name': 'Partner individual',
            'is_company': True,
            'email': 'partner_individual@example.org',
        })
        self.partner_employee = self.env['res.partner'].create({
            'name': 'Employee',
            'email': 'employee@example.org',
        })

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def get_file_name(self, fname):
        return fname.split('/')[-1:][0]

    def test_import_create_base_ok(self):
        group_portal_id = self.env.ref('base.group_portal').id
        group_employee_id = self.env.ref('base.group_user').id
        fname = self.get_sample('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_user.template_user').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        user_partner = self.env['res.users'].search([
            ('name', '=', 'User partner 1'),
        ])
        self.assertEquals(len(user_partner), 0)
        user_contact = self.env['res.users'].search([
            ('name', '=', 'User contact 1'),
        ])
        self.assertEquals(len(user_contact), 0)
        partners_1_2 = self.env['res.users'].search([
            ('name', '=', 'Invoice address'),
        ])
        self.assertEquals(len(partners_1_2), 0)
        partners_2 = self.env['res.users'].search([
            ('name', '=', 'User 3'),
        ])
        self.assertEquals(len(partners_2), 0)
        employee = self.env['res.users'].search([
            ('name', '=', 'Employee'),
        ])
        self.assertEquals(len(employee), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        user_partner = self.env['res.users'].search([
            ('name', '=', 'User partner 1'),
        ])
        self.assertEquals(len(user_partner), 1)
        self.assertEquals(user_partner.login, 'partner@example.org')
        self.assertIn(group_portal_id, user_partner.groups_id.ids)
        user_contact = self.env['res.users'].search([
            ('name', '=', 'User contact 1'),
        ])
        self.assertEquals(len(user_contact), 1)
        self.assertEquals(user_contact.login, 'partner_contact@example.org')
        self.assertIn(group_portal_id, user_contact.groups_id.ids)
        user_3 = self.env['res.users'].search([
            ('name', '=', 'User 3'),
        ])
        self.assertEquals(len(user_3), 1)
        self.assertEquals(user_3.login, 'partner_individual@example.org')
        self.assertIn(group_portal_id, user_3.groups_id.ids)
        employee = self.env['res.users'].search([
            ('name', '=', 'Employee'),
        ])
        self.assertEquals(len(employee), 1)
        self.assertEquals(employee.login, 'employee@example.org')
        self.assertEquals(employee.lang, False)
        self.assertIn(group_employee_id, employee.groups_id.ids)

    def test_import_write_base_ok(self):
        group_employee_id = self.env.ref('base.group_user').id
        group_portal_id = self.env.ref('base.group_portal').id
        self.env['res.users'].create({
            'name': 'User write test',
            'login': 'partner@example.org',
        })
        fname = self.get_sample('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_user.template_user').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        user_partner = self.env['res.users'].search([
            ('login', '=', 'partner@example.org'),
        ])
        self.assertEquals(len(user_partner), 1)
        self.assertEquals(user_partner.name, 'User write test')
        self.assertIn(group_employee_id, user_partner.groups_id.ids)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        user_partner = self.env['res.users'].search([
            ('login', '=', 'partner@example.org'),
        ])
        self.assertEquals(len(user_partner), 1)
        self.assertEquals(user_partner.name, 'User partner 1')
        self.assertEquals(user_partner.login, 'partner@example.org')
        self.assertIn(group_portal_id, user_partner.groups_id.ids)

    def test_import_create_required_fields(self):
        fname = self.get_sample('sample_required_fields.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_user.template_user').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        self.assertIn(_(
            '3: The \'login\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'name\' field is required.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '3: The \'login\' field is required.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '5: The \'name\' field is required.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '6: The \'login\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[4].name)
        self.assertIn(_(
            '6: The \'login\' field is required.'), wizard.line_ids[5].name)
        user_1 = self.env['res.users'].search([
            ('name', '=', 'User partner 1'),
        ])
        self.assertEquals(len(user_1), 0)
        contact_1 = self.env['res.users'].search([
            ('name', '=', 'User contact 1'),
        ])
        self.assertEquals(len(contact_1), 0)
        employee = self.env['res.users'].search([
            ('name', '=', 'Employee'),
        ])
        self.assertEquals(len(employee), 0)
        noname = self.env['res.users'].search([
            ('login', '=', 'partner_individual@example.org'),
        ])
        self.assertEquals(len(noname), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        self.assertIn(_(
            '3: The \'login\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'name\' field is required.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '3: The \'login\' field is required.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '5: The \'name\' field is required.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '6: The \'login\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[4].name)
        self.assertIn(_(
            '6: The \'login\' field is required.'), wizard.line_ids[5].name)
        user_1 = self.env['res.users'].search([
            ('name', '=', 'User partner 1'),
        ])
        self.assertEquals(len(user_1), 1)
        contact_1 = self.env['res.users'].search([
            ('name', '=', 'User contact 1'),
        ])
        self.assertEquals(len(contact_1), 1)
        employee = self.env['res.users'].search([
            ('name', '=', 'Employee'),
        ])
        self.assertEquals(len(employee), 0)
        noname = self.env['res.users'].search([
            ('login', '=', 'partner_individual@example.org'),
        ])
        self.assertEquals(len(noname), 0)

    def test_import_write_required_fields(self):
        group_portal_id = self.env.ref('base.group_portal').id
        self.env['res.users'].create({
            'name': 'User write test',
            'login': 'partner@example.org',
        })
        fname = self.get_sample('sample_required_fields.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_user.template_user').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        self.assertIn(_(
            '3: The \'login\' field is required, you must fill it with a valid '
            'value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'name\' field is required.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '3: The \'login\' field is required.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '5: The \'name\' field is required.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '6: The \'login\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[4].name)
        self.assertIn(_(
            '6: The \'login\' field is required.'), wizard.line_ids[5].name)
        user_1 = self.env['res.users'].search([
            ('name', '=', 'User write test'),
        ])
        self.assertEquals(len(user_1), 1)
        contact_1 = self.env['res.users'].search([
            ('name', '=', 'User contact 1'),
        ])
        self.assertEquals(len(contact_1), 0)
        employee = self.env['res.users'].search([
            ('name', '=', 'Employee'),
        ])
        self.assertEquals(len(employee), 0)
        noname = self.env['res.users'].search([
            ('login', '=', 'partner_individual@example.org'),
        ])
        self.assertEquals(len(noname), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        self.assertIn(_(
            '3: The \'login\' field is required, you must fill it with a valid '
            'value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'name\' field is required.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '3: The \'login\' field is required.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '5: The \'name\' field is required.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '6: The \'login\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[4].name)
        self.assertIn(_(
            '6: The \'login\' field is required.'), wizard.line_ids[5].name)
        user_1 = self.env['res.users'].search([
            ('name', '=', 'User partner 1'),
        ])
        self.assertEquals(len(user_1), 1)
        self.assertEquals(user_1.login, 'partner@example.org')
        self.assertIn(group_portal_id, user_1.groups_id.ids)

    def test_import_create_wrong_values(self):
        fname = self.get_sample('sample_wrong_values.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_user.template_user').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '4: The \'login\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: The \'login\' field is required.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '5: The \'name\' field is required.'), wizard.line_ids[2].name)
        user_1 = self.env['res.users'].search([
            ('name', '=', 'User partner 1'),
        ])
        self.assertEquals(len(user_1), 0)
        contact_1 = self.env['res.users'].search([
            ('name', '=', 'User contact 1'),
        ])
        self.assertEquals(len(contact_1), 0)
        user_3 = self.env['res.users'].search([
            ('name', '=', 'User 3'),
        ])
        self.assertEquals(len(user_3), 0)
        noname = self.env['res.users'].search([
            ('login', '=', 'employee@example.org'),
        ])
        self.assertEquals(len(noname), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '4: The \'login\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: The \'login\' field is required.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '5: The \'name\' field is required.'), wizard.line_ids[2].name)
        contact_1 = self.env['res.users'].search([
            ('name', '=', 'User contact 1'),
        ])
        self.assertEquals(len(contact_1), 1)
        user_3 = self.env['res.users'].search([
            ('name', '=', 'User 3'),
        ])
        self.assertEquals(len(user_3), 0)
        noname = self.env['res.users'].search([
            ('login', '=', 'employee@example.org'),
        ])
        self.assertEquals(len(noname), 0)

    def test_import_write_wrong_values(self):
        self.env['res.users'].create({
            'name': 'employee',
            'login': 'employee@example.org',
        })
        fname = self.get_sample('sample_wrong_values.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_user.template_user').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '4: The \'login\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: The \'login\' field is required.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '5: The \'name\' field is required.'), wizard.line_ids[2].name)
        user_1 = self.env['res.users'].search([
            ('name', '=', 'User partner 1'),
        ])
        self.assertEquals(len(user_1), 0)
        contact_1 = self.env['res.users'].search([
            ('name', '=', 'User contact 1'),
        ])
        self.assertEquals(len(contact_1), 0)
        user_3 = self.env['res.users'].search([
            ('name', '=', 'User 3'),
        ])
        self.assertEquals(len(user_3), 0)
        wrong_name = self.env['res.users'].search([
            ('login', '=', 'employee@example.org'),
        ])
        self.assertEquals(len(wrong_name), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '4: The \'login\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '4: The \'login\' field is required.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '5: The \'name\' field is required.'), wizard.line_ids[2].name)
        user_1 = self.env['res.users'].search([
            ('name', '=', 'User partner 1'),
        ])
        self.assertEquals(len(user_1), 1)
        contact_1 = self.env['res.users'].search([
            ('name', '=', 'User contact 1'),
        ])
        self.assertEquals(len(contact_1), 1)
        user_3 = self.env['res.users'].search([
            ('name', '=', 'User 3'),
        ])
        self.assertEquals(len(user_3), 0)
        wrong_name = self.env['res.users'].search([
            ('login', '=', 'employee@example.org'),
        ])
        self.assertEquals(len(wrong_name), 1)
        self.assertEquals(wrong_name.name, 'employee')
