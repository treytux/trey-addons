# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _
from functools import partial
import math
import logging
_log = logging.getLogger(__name__)


class ReportPrintFormatsPickingValued(models.TransientModel):
    _name = 'report.print_formats_picking_valued.report_picking_valued'

    @api.multi
    def get_price(self, line):
        '''Line can be a stock move or a pack operation.'''
        if not line.picking_id.sale_id.exists():
            return line.product_id.lst_price
        pricelist = None
        if line.picking_id.sale_id:
            pricelist = line.picking_id.sale_id.pricelist_id
        if 'purchase_line_id' in line and line.purchase_line_id:
            pricelist = line.purchase_line_id.order_id.pricelist_id
        if (line.picking_id.partner_id and
                line.picking_id.partner_id.property_product_pricelist):
            pricelist = (
                line.picking_id.partner_id.property_product_pricelist)
        if not pricelist:
            raise exceptions.Warning(_('There is not pricelist'))

        if line._name == 'stock.pack.operation':
            qty = line.product_qty
        else:
            qty = line.product_uom_qty
        return pricelist.price_get(
            line.product_id.id, qty, line.picking_id.partner_id.id)[
            pricelist.id]

    def monetary_format(self, amount):
        cr, uid, context = self.env.args
        company = self.env['res.company'].search([])[0]
        currency = company.currency_id
        lang_code = context.get('lang') or 'en_US'
        lang = self.env['res.lang'].search([('code', '=', lang_code)])
        precision = int(round(math.log10(currency.rounding)))
        fmt = "%.{0}f".format(-precision if precision < 0 else 0)
        formatted_amount = lang.format(
            fmt, currency.round(amount), grouping=True, monetary=True)
        return formatted_amount

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        picking_obj_obj = self.env['stock.picking']
        report = report_obj._get_report_from_name(
            'print_formats_picking_valued.report_picking_valued')
        selected_picking_objs = picking_obj_obj.browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': selected_picking_objs,
            'get_price': partial(self.get_price),
            'monetary_format': partial(self.monetary_format)}
        report = report_obj.browse(self.ids[0])
        return report.render(
            'print_formats_picking_valued.report_picking_valued', docargs)
