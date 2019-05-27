# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class ReportStockPickingDeliveryFormCarrierCollect(models.TransientModel):
    _name = 'report.stock_picking_delivery_form.carrier_collect'

    def get_pickings(self, collect):
        if not collect.carrier_id.group_collect_by_partner:
            return collect.picking_ids
        partner_groups = {}
        for pick in collect.picking_ids:
            partner_groups.setdefault(pick.partner_id.id, []).append(pick)
        return partner_groups.values()

    @api.multi
    def render_html(self, data=None):
        template = 'stock_picking_delivery_form.carrier_collect'
        doc = self.env['report']._get_report_from_name(template)
        report = self.env['report'].browse(self.ids[0])
        return report.render(template, {
            'doc_ids': self.ids,
            'doc_model': doc.model,
            'docs': self.env[doc.model].browse(self.ids),
            'get_pickings': self.get_pickings})
