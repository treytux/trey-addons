# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import _, api, fields, models


class MrpBomRecalculatePrice(models.TransientModel):
    _name = 'mrp.bom.recalculate_price'
    _description = 'Bom Price Recalculate'

    log = fields.Text(
        string='Log',
    )
    state = fields.Selection(
        string='State',
        selection=[
            ('step1', 'Step1'),
            ('done', 'Done'),
        ],
        required=True,
        default='step1',
    )

    @api.multi
    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }

    @api.multi
    def recalculate_bom_price(self):
        active_ids = self.env.context['active_ids']
        booms = self.env['mrp.bom'].browse(active_ids)
        if not booms:
            return
        ctx = self.env.context.copy()
        ctx['update_from_wizard'] = True
        booms.run_update_prices()
        log = _('Update %s Templates and their variants' % len(active_ids))
        self.write({
            'state': 'done',
            'log': log,
        })
        return self._reopen_view()
