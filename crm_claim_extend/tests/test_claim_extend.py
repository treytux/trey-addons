# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp.tests.common import TransactionCase
import logging
_log = logging.getLogger(__name__)


class CrmClaimExtendCase(TransactionCase):

    def setUp(self):
        super(CrmClaimExtendCase, self).setUp()
        self.claim_01 = self.env['crm.claim'].create({'name': 'Claim 01'})

    def test_00_crm_claim_extend(self):
        '''Check the state initially.'''
        self.assertEqual(self.claim_01.state, 'draft')

    def test_01_crm_claim_extend(self):
        '''Change the states of a claim until 'done' and check it.'''
        # From 'draft' to 'progress'
        self.claim_01.to_progress()
        self.assertEqual(self.claim_01.state, 'progress')
        # From 'progress' to 'pending_material'
        self.claim_01.to_pending_material()
        self.assertEqual(self.claim_01.state, 'pending_material')
        # From 'pending_material' to 'progress'
        self.claim_01.to_progress()
        self.assertEqual(self.claim_01.state, 'progress')
        # From 'progress' to 'done'
        self.claim_01.to_done()
        self.assertEqual(self.claim_01.state, 'done')

    def test_02_crm_claim_extend(self):
        '''Change the states of a claim until 'exception' and check it.'''
        # From 'draft' to 'progress'
        self.claim_01.to_progress()
        self.assertEqual(self.claim_01.state, 'progress')
        # From 'progress' to 'pending_material'
        self.claim_01.to_pending_material()
        self.assertEqual(self.claim_01.state, 'pending_material')
        # From 'pending_material' to 'progress'
        self.claim_01.to_progress()
        self.assertEqual(self.claim_01.state, 'progress')
        # From 'progress' to 'exception'
        self.claim_01.to_exception()
        self.assertEqual(self.claim_01.state, 'exception')
