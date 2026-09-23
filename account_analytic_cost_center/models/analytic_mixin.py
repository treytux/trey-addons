###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AnalyticMixin(models.AbstractModel):
    _inherit = 'analytic.mixin'

    analytic_distribution_cost_center = fields.Json(
        string='Analytic cost center',
        compute='_compute_analytic_distribution',
        store=True,
        copy=True,
        readonly=False,
        precompute=True,
    )
