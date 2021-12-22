###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPartnerZone(TransactionCase):

    def test_partner_zone(self):
        zone_a = self.env['res.partner.zone'].create({
            'name': 'Zone A',
        })
        self.assertEquals(zone_a.partner_count, 0)
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'zone_id': zone_a.id,
        })
        self.assertEquals(partner.zone_id, zone_a)
        self.assertEquals(zone_a.partner_count, 1)
        user_zone = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'company_ids': [(6, 0, [self.env.user.company_id.id])],
            'company_id': self.env.user.company_id.id,
            'zone_ids': [(6, 0, [zone_a.id])],
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
            ])],
        })
        partners = self.env['res.partner'].search(
            [('zone_id', '=', zone_a.id)])
        self.assertIn(partner.id, partners.ids)
        partners_noaccess = self.env['res.partner'].sudo(user_zone.id).search(
            [('zone_id', '=', zone_a.id)])
        self.assertIn(partner.id, partners_noaccess.ids)
        # @TODO fix ir.rules for read only partners with the same
        # user_zone.zone_ids = [(6, 0, [])]
        # partners_noaccess = self.env['res.partner'].sudo(
        #     user_zone.id).search([('zone_id', '=', zone_a.id)])
        # self.assertNotIn(partner.id, partners_noaccess.ids)
