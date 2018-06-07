# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    total2produce_count = fields.Float(
        compute='_compute_total2produce',
        string='Total to produce',
        store=False)

    @api.one
    def _compute_total2produce(self):
        try:
            active_model = self._name
            active_id = self.ids[0]
            fields = ['line_ids', 'real_qty2produce', 'virtual_qty2produce']
            res = self.env['wiz.mrp.simulation'].with_context(
                active_id=active_id, active_model=active_model).default_get(
                    fields)
            self.total2produce_count = res['real_qty2produce']
        except Exception:
            self.total2produce_count = 0
