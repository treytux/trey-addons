###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPartnerZone(TransactionCase):

    def test_partner_zone(self):
        zone_a = self.env['res.partner.zone'].create({
            'name': 'Zone A',
        })
        zone_b = self.env['res.partner.zone'].create({
            'name': 'Zone A',
        })
        self.assertEquals(zone_a.partner_count, 0)
        self.assertEquals(zone_b.partner_count, 0)
        partner_a = self.env['res.partner'].create({
            'name': 'Partner test A',
            'zone_id': zone_a.id,
        })
        partner_b = self.env['res.partner'].create({
            'name': 'Partner test B',
            'zone_id': zone_b.id,
        })
        self.assertEquals(partner_a.zone_id, zone_a)
        self.assertEquals(partner_b.zone_id, zone_b)
        self.assertEquals(zone_a.partner_count, 1)
        self.assertEquals(zone_b.partner_count, 1)
        user_zone_a = self.env['res.users'].create({
            'name': 'User Zone A',
            'login': 'user@test.com',
            'company_ids': [(6, 0, [self.env.user.company_id.id])],
            'company_id': self.env.user.company_id.id,
            'zone_ids': [(6, 0, [zone_a.id])],
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
            ])],
        })
        partners_zone_a = self.env['res.partner'].search(
            [('zone_id', '=', zone_a.id)])
        self.assertIn(partner_a.id, partners_zone_a.ids)
        self.assertNotIn(partner_b.id, partners_zone_a.ids)
        partners_user_zone_a = self.env['res.partner'].sudo(
            user_zone_a.id).search([])
        self.assertIn(partner_a.id, partners_user_zone_a.ids)
        self.assertNotIn(partner_b.id, partners_user_zone_a.ids)
        user_zone_a.zone_ids = [(6, 0, [])]
        partners_user_zone_a = self.env['res.partner'].sudo(
            user_zone_a.id).search([])
        self.assertNotIn(partner_a.id, partners_user_zone_a.ids)
        self.assertNotIn(partner_b.id, partners_user_zone_a.ids)
        group_zone = self.env.ref('partner_zone.group_all_partners_zone')
        group_zone.write({'users': [(4, user_zone_a.id)]})
        partners_user_zone_a = self.env['res.partner'].sudo(
            user_zone_a.id).search([])
        self.assertIn(partner_a.id, partners_user_zone_a.ids)
        self.assertIn(partner_b.id, partners_user_zone_a.ids)
        group_zone.write({'users': [(3, user_zone_a.id)]})
        partners_user_zone_a = self.env['res.partner'].sudo(
            user_zone_a.id).search([])
        self.assertNotIn(partner_a.id, partners_user_zone_a.ids)
        self.assertNotIn(partner_b.id, partners_user_zone_a.ids)

    def test_private_contact(self):
        user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'company_ids': [(6, 0, [self.env.user.company_id.id])],
            'company_id': self.env.user.company_id.id,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
            ])],
        })
        partner = self.env['res.partner'].create({
            'name': 'Partner',
        })
        partner_contact = self.env['res.partner'].create({
            'name': 'Partner Contact',
            'parent_id': partner.id,
        })
        private_contact = self.env['res.partner'].create({
            'name': 'Private User Contact',
            'parent_id': user.partner_id.id,
            'type': 'private',
        })
        self.assertEquals(partner.id, partner_contact.parent_id.id)
        partners = self.env['res.partner'].sudo(user.id).search([])
        self.assertIn(user.partner_id.id, partners.ids)
        self.assertNotIn(private_contact.id, partners.ids)
        self.assertNotIn(partner.id, partners.ids)
        self.assertNotIn(partner_contact.id, partners.ids)
        group_zone = self.env.ref('base.group_private_addresses')
        group_zone.write({'users': [(4, user.id)]})
        partners = self.env['res.partner'].sudo(user.id).search([])
        self.assertIn(user.partner_id.id, partners.ids)
        self.assertIn(private_contact.id, partners.ids)
        self.assertNotIn(partner.id, partners.ids)
        self.assertNotIn(partner_contact.id, partners.ids)
