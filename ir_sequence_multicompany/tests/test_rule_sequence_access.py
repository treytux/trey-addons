###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import AccessError
from odoo.tests import common


class TestIrSequenceMultiCompany(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.company_a = self.env['res.company'].create({
            'name': 'Test Company A',
        })
        self.company_b = self.env['res.company'].create({
            'name': 'Test Company B',
        })
        self.user_a = self.env['res.users'].create({
            'name': 'User Company A',
            'login': 'user_a_test',
            'password': 'test',
            'company_id': self.company_a.id,
            'company_ids': [(6, 0, [self.company_a.id])],
        })
        self.seq_company_a = self.env['ir.sequence'].create({
            'name': 'Seq Company A',
            'code': 'seq.a',
            'company_id': self.company_a.id,
        })
        self.seq_company_b = self.env['ir.sequence'].create({
            'name': 'Seq Company B',
            'code': 'seq.b',
            'company_id': self.company_b.id,
        })
        self.seq_global = self.env['ir.sequence'].create({
            'name': 'Global Sequence',
            'code': 'seq.global',
            'company_id': False,
        })

    def test_user_sees_own_company_and_global_sequences(self):
        sequences = self.env['ir.sequence'].with_user(self.user_a).search([])
        self.assertTrue(
            all(name in [self.seq_global.name, self.seq_company_a.name] for
                name in sequences.mapped('name')))

    def test_user_cannot_read_company_b_sequence_directly(self):
        with self.assertRaises(AccessError) as result:
            self.env['ir.sequence'].with_user(self.user_a).browse(
                self.seq_company_b.id).read(['name'])
        self.assertIn(
            'Due to security restrictions, you are not allowed to access'
            ' \'Sequence\' (ir.sequence) records', result.exception.name)

    def test_user_cannot_write_company_b_sequence(self):
        with self.assertRaises(AccessError) as result:
            self.env['ir.sequence'].with_user(self.user_a).browse(
                self.seq_company_b.id).write({'name': 'New Name'})
        self.assertIn(
            'Due to security restrictions, you are not allowed to access'
            ' \'Sequence\' (ir.sequence) records', result.exception.name)

    def test_user_cannot_unlink_company_b_sequence(self):
        with self.assertRaises(AccessError) as result:
            self.env['ir.sequence'].with_user(self.user_a).browse(
                self.seq_company_b.id).unlink()
        self.assertIn(
            'You are not allowed to delete \'Sequence\' (ir.sequence) records',
            result.exception.name)
