# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    total_gross = fields.Float(
        string='Total Gross',
        help='Sum of purchase value for this asset and all his children.',
        compute='_compute_total_gross')
    total_residual = fields.Float(
        string='Total Residual',
        help='Sum of redidual value for this asset and all his children.',
        compute='_compute_total_residual')
    total_amortized = fields.Float(
        string='Total Amortized',
        help='Sum of balance entries for this asset and all his children.',
        compute='_compute_total_amortized')

    @api.one
    def _compute_total_gross(self):
        if not self.child_ids:
            self.total_gross = self.purchase_value
            return
        self.total_gross = self.purchase_value + sum(
            [l.purchase_value for l in self.child_ids])

    @api.one
    def _compute_total_residual(self):
        if not self.child_ids:
            self.total_residual = self.value_residual
            return
        self.total_residual = self.value_residual + sum(
            [l.value_residual for l in self.child_ids])

    @api.one
    def _compute_total_amortized(self):
        main_amortized = (
            (self.purchase_value - self.salvage_value) - self.value_residual)
        if not self.child_ids:
            self.total_amortized = main_amortized
            return
        child_amortized = sum(
            [(l.purchase_value - l.salvage_value) - l.value_residual
             for l in self.child_ids])
        self.total_amortized = main_amortized + child_amortized
