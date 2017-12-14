# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
import logging
_log = logging.getLogger(__name__)


class TestSetIssue(common.TransactionCase):

    def setUp(self):
        super(TestSetIssue, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner for test project_issue_stock_moves',
            'is_company': True,
            'customer': True})
        self.product = self.env['product.product'].create({
            'name': 'Product for test project_issue_stock_moves'})
        self.project = self.env['project.project'].create({
            'name': 'Proyect for test project_issue_stock_moves',
            'use_issues': True,
            'partner_id': self.partner.id})
        self.issue = self.env['project.issue'].create({
            'name': 'Issue for test project_issue_stock_moves',
            'project_id': self.project.id})
        self.issue2 = self.env['project.issue'].create({
            'name': 'Issue second for test project_issue_stock_moves',
            'project_id': self.project.id})

    def test_picking(self):
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing')])[0]
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'issue_id': self.issue.id,
            'invoice_state': '2binvoiced',
            'picking_type_id': picking_type.id})
        self.assertEquals(picking.issue_id, self.issue)

        location = self.env.ref('stock.stock_location_customers')
        move = self.env['stock.move'].create({
            'picking_id': picking.id,
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'location_id': location.id,
            'location_dest_id': location.id,
            'product_uom_qty': 1})
        self.assertEquals(move.issue_id, picking.issue_id)

        # Test counters
        self.issue = self.env['project.issue'].browse(self.issue.id)
        self.assertEquals(self.issue.picking_count, 1)
        self.assertEquals(self.issue.move_count, 1)

        # Tests write picking
        picking.issue_id = self.issue2.id
        move = self.env['stock.move'].browse(move.id)
        self.assertEqual(picking.issue_id, move.issue_id)

        # Tests write move, not set issue_id to picking
        move.issue_id = self.issue.id
        picking = self.env['stock.picking'].browse(picking.id)
        self.assertNotEqual(move.issue_id, picking.issue_id)
