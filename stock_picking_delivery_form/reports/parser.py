# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class DeliveryCarrierCollectReport(models.TransientModel):
    _name = 'report.delivery.carrier.collect.report'

    @api.multi
    def render_html(self, data=None):
        report = self.env['report']._get_report_from_name(
            'stock_picking_delivery_form.carrier_collect')
        return report.render('stock_picking_delivery_form.carrier_collect', {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(self.ids)})
