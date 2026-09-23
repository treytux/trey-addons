###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestIrAttachmentDeleteRule(TransactionCase):

    def setUp(self):
        super().setUp()
        self.user_allow_delete = self.env['res.users'].create({
            'name': 'Test allow delete attachemnts',
            'login': 'user_allow_delete@test.com',
            'company_ids': [(6, 0, [self.env.user.company_id.id])],
            'company_id': self.env.user.company_id.id,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('base.group_partner_manager').id,
                self.env.ref(
                    'ir_attachment_delete_rule.'
                    'ir_attachment_allow_delete_group'
                ).id,
            ])],
        })
        self.user_not_allow_delete = self.env['res.users'].create({
            'name': 'Test not allow delete attachemnts',
            'login': 'user_not_allow_delete@test.com',
            'company_ids': [(6, 0, [self.env.user.company_id.id])],
            'company_id': self.env.user.company_id.id,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('base.group_partner_manager').id,
            ])],
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })

    def test_allow_delete_attachment(self):
        attachment = self.env['ir.attachment'].sudo(
            self.user_allow_delete
        ).create({
            'name': 'Test attachment',
            'type': 'binary',
        })
        attachment.sudo(self.user_allow_delete).unlink()
        self.assertFalse(
            self.env['ir.attachment'].search([('id', '=', attachment.id)]))

    def test_not_allow_delete_attachment(self):
        attachment = self.env['ir.attachment'].sudo(
            self.user_not_allow_delete
        ).create({
            'name': 'Test attachment',
            'type': 'binary',
        })
        with self.assertRaises(AccessError):
            attachment.sudo(self.user_not_allow_delete).unlink()
        self.assertTrue(
            self.env['ir.attachment'].search([('id', '=', attachment.id)]))

    def test_allow_delete_register_with_attachment(self):
        self.env['ir.attachment'].sudo(
            self.user_allow_delete
        ).create({
            'name': 'Test attachment',
            'type': 'binary',
            'res_model': 'res.partner',
            'res_id': self.partner.id,
        })
        self.partner.sudo(self.user_allow_delete).unlink()
        self.assertFalse(
            self.env['res.partner'].search([('id', '=', self.partner.id)]))

    def test_not_allow_delete_register_with_attachment(self):
        attachment = self.env['ir.attachment'].sudo(
            self.user_not_allow_delete
        ).create({
            'name': 'Test attachment',
            'type': 'binary',
            'res_model': 'res.partner',
            'res_id': self.partner.id,
        })
        with self.assertRaises(AccessError):
            self.partner.sudo(self.user_not_allow_delete).unlink()
        self.assertTrue(
            self.env['ir.attachment'].search([('id', '=', attachment.id)]))
        self.assertFalse(
            self.env['res.partner'].search([('id', '=', self.partner.id)]))
