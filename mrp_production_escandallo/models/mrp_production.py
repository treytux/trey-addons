###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_report_mrp_bom_overview(self):
        self.ensure_one()
        action = self.sudo().env.ref('mrp.action_report_mrp_bom')
        res = action.read()[0]
        res.update({
            'res_id': self.bom_id.id,
            'context': {
                'active_model': 'mrp.bom',
                'active_id': self.bom_id.id,
                'active_ids': [self.bom_id],
            },
        })
        return res
