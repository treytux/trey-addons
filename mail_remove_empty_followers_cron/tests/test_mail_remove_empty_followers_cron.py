###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestMailRemoveEmptyFollowersCron(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.partner2 = self.env['res.partner'].create({
            'name': 'Partner test2',
        })
        self.partner3 = self.env['res.partner'].create({
            'name': 'Partner test3',
            'email': 'partner@partner.com',
        })
        self.partner4 = self.env['res.partner'].create({
            'name': 'Partner test4',
        })
        self.partner5 = self.env['res.partner'].create({
            'name': 'Partner test5',
            'email': 'partner@partner.com',
        })

    def test_remove_empty_followers(self):
        self.partner.message_subscribe(self.partner2.ids)
        self.partner.message_subscribe(self.partner3.ids)
        self.partner.message_subscribe(self.partner4.ids)
        self.partner.message_subscribe(self.partner5.ids)
        self.assertEquals(len(self.partner.message_follower_ids), 5)
        self.partner.remove_empty_followers('res.partner')
        self.assertEquals(len(self.partner.message_follower_ids), 3)
        self.assertTrue(self.partner.message_follower_ids[0].partner_id.email)
        self.assertTrue(self.partner.message_follower_ids[1].partner_id.email)
        self.assertTrue(self.partner.message_follower_ids[2].partner_id.email)
