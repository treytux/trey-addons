###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def action_mrp_finished_product_details(self):
        self.ensure_one()
        wizard = self.env['mrp.production.finished_detail'].create_wizard(
            self._context['default_production_id'], self.product_id.id)
        action = self.env.ref(
            'mrp_production_finished_products.'
            'mrp_production_finished_detail_action').read()[0]
        action['res_id'] = wizard.id
        return action
