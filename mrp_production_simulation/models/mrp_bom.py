###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    total2produce_count = fields.Float(
        compute='_compute_total2produce',
        string='Total to produce',
        store=False,
    )

    def _compute_total2produce(self):
        for bom in self:
            try:
                active_model = bom._name
                active_id = bom.ids[0]
                fields = [
                    'line_ids', 'real_qty2produce', 'virtual_qty2produce']
                res = self.env['wiz.mrp.simulation'].with_context(
                    active_id=active_id,
                    active_model=active_model
                ).default_get(fields)
                bom.total2produce_count = res['real_qty2produce']
            except Exception:
                bom.total2produce_count = 0
