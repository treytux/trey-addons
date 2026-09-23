###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    use_management = fields.Boolean(
        related='product_id.product_tmpl_id.use_management',
    )
    number_of_uses = fields.Integer(
        string='Number of uses',
        default=1,
    )
    times_used = fields.Integer(
        string='Times used',
    )
    pending_uses = fields.Integer(
        string='Pending uses',
        compute='_compute_pending_uses',
    )
    qc_use_dates = fields.One2many(
        comodel_name='qc.use.date',
        inverse_name='lot_id',
        string='Use dates',
    )

    @api.depends('number_of_uses', 'times_used')
    def _compute_pending_uses(self):
        for lot in self:
            if lot.product_id.use_management:
                lot.pending_uses = (
                    lot.number_of_uses - lot.times_used)
                if lot.pending_uses == 0:
                    if len(lot.product_id.product_tmpl_id.qc_test_ids) == 0:
                        self.env['qc.inspection'].create({
                            'name': 'Inspection Test',
                            'object_id': '%s,%d' % (lot._name, lot.id),
                        })
                        continue
                    for test in lot.product_id.product_tmpl_id.qc_test_ids:
                        inspection = self.env['qc.inspection'].create({
                            'name': 'Inspection test',
                            'object_id': '%s,%d' % (lot._name, lot.id),
                        })
                        wizard = self.env['qc.inspection.set.test'].create({
                            'test': test.id
                        })
                        wizard.with_context(
                            active_id=inspection.id).action_create_test()
