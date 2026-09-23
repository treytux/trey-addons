###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestCrmTeamPlannedRevenueTarget(TransactionCase):
    def setUp(self):
        super().setUp()
        self.team_a = self.env['crm.team'].create({
            'name': 'Test Sales Team A',
            'team_type': 'sales',
            'use_planned_revenue': True,
            'planned_revenue_target': 10000,
        })
        self.team_b = self.env['crm.team'].create({
            'name': 'Test Sales Team B',
            'team_type': 'sales',
            'use_planned_revenue': True,
            'planned_revenue_target': 50000,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'customer': True,
            'is_company': True,
        })

    def test_team_planned_revenue(self):
        self.env['crm.lead'].create({
            'name': 'Test lead 1',
            'planned_revenue': 10000,
            'probability': 10,
            'partner_id': self.partner.id,
            'team_id': self.team_a.id,
        })
        self.env['crm.lead'].create({
            'name': 'Test lead 2',
            'planned_revenue': 10000,
            'probability': 50,
            'partner_id': self.partner.id,
            'team_id': self.team_a.id,
        })
        self.assertEquals(self.team_a.planned_revenue , 6000)
        self.assertEquals(self.team_a.planned_revenue_target , 10000)

    def test_team_planned_revenue_with_won_lead(self):
        self.env['crm.lead'].create({
            'name': 'Test lead 1',
            'planned_revenue': 50000,
            'probability': 10,
            'partner_id': self.partner.id,
            'team_id': self.team_a.id,
        })
        self.env['crm.lead'].create({
            'name': 'Test lead 2',
            'planned_revenue': 10000,
            'probability': 100,
            'partner_id': self.partner.id,
            'team_id': self.team_a.id,
        })
        self.assertEquals(self.team_a.planned_revenue , 5000)
        self.assertEquals(self.team_a.planned_revenue_target , 10000)

    def test_team_planned_revenue_with_other_team(self):
        self.env['crm.lead'].create({
            'name': 'Test lead 1',
            'planned_revenue': 70000,
            'probability': 10,
            'partner_id': self.partner.id,
            'team_id': self.team_a.id,
        })
        self.env['crm.lead'].create({
            'name': 'Test lead 2',
            'planned_revenue': 10000,
            'probability': 50,
            'partner_id': self.partner.id,
            'team_id': self.team_b.id,
        })
        self.assertEquals(self.team_a.planned_revenue , 7000)
        self.assertEquals(self.team_b.planned_revenue , 5000)
        self.assertEquals(self.team_a.planned_revenue_target , 10000)
        self.assertEquals(self.team_b.planned_revenue_target , 50000)
