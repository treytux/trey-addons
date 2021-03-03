# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    diff_credit = fields.Float(
        string='Diff credit',
        compute='_compute_credit_note',
        help='Credit limit - balance.',
    )
    info_credit_note = fields.Text(
        string='Info credit note',
        translate=True,
        compute='_compute_credit_note',
        help='Credit limit - balance.',
    )
    warn_credit_note = fields.Text(
        string='Warning credit note',
        translate=True,
        compute='_compute_credit_note',
    )

    @api.multi
    def onchange_partner_id(self, partner_id):
        res = super(PosOrder, self).onchange_partner_id(partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            warning = partner.check_warning_credit_limit(self)
            if warning:
                res.update(warning)
        return res

    @api.one
    @api.depends(
        'amount_total', 'lines', 'partner_id', 'partner_id.credit',
        'partner_id.credit_limit')
    def _compute_credit_note(self):
        partner = self.partner_id
        if not partner or partner.credit_limit == 0.0:
            self.diff_credit = 0.0
            self.info_credit_note = ''
            self.warn_credit_note = ''
            return
        self.diff_credit, self.info_credit_note, self.warn_credit_note = (
            partner.fill_credit_note_msgs(self))
