# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from functools import partial
from openerp.osv import osv
from openerp import exceptions, _
from reportlab.graphics.barcode import createBarcodeDrawing


class PartnerReport(osv.AbstractModel):
    _name = 'report.repair_workorder.partner_report'

    def get_total(self, cr, uid, workorder, context=None):
        total = 0
        for line_consumed in workorder.consumed_ids:
            total += line_consumed.quantity * line_consumed.price_unit
        return total

    def render_html(self, cr, uid, ids, data=None, context=None):
        report_obj = self.pool['report']
        repair_workorder_obj = self.pool['repair.workorder']
        report = report_obj._get_report_from_name(
            cr, uid, 'repair_workorder.partner_report')
        selected_orders = repair_workorder_obj.browse(
            cr, uid, ids, context=context)

        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': selected_orders,
            'get_total': partial(
                self.get_total, cr, uid, context=context),
            'printBarcode': partial(
                self.printBarcode, cr, uid, context=context),
        }

        return report_obj.render(
            cr, uid, ids, 'repair_workorder.partner_report',
            docargs, context=context)

    def printBarcode(self, cr, uid, value, width, height, context=None):
        try:
            width, height = int(width), int(height)
            barcode = createBarcodeDrawing(
                'EAN13', value=value, format='png', width=width, height=height)
            barcode = barcode.asString('png')
            barcode = barcode.encode('base64', 'strict')
        except (ValueError, AttributeError):
            raise exceptions.Warning(_('Cannot convert into barcode.'))

        return barcode


class CompanyReport(osv.AbstractModel):
    _name = 'report.repair_workorder.company_report'

    def get_total(self, cr, uid, workorder, context=None):
        total = 0
        for line_consumed in workorder.consumed_ids:
            total += line_consumed.quantity * line_consumed.price_unit
        return total

    def render_html(self, cr, uid, ids, data=None, context=None):
        report_obj = self.pool['report']
        repair_workorder_obj = self.pool['repair.workorder']
        report = report_obj._get_report_from_name(
            cr, uid, 'repair_workorder.company_report')
        selected_orders = repair_workorder_obj.browse(
            cr, uid, ids, context=context)

        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': selected_orders,
            'get_total': partial(
                self.get_total, cr, uid, context=context),
            'printBarcode': partial(
                self.printBarcode, cr, uid, context=context),
        }
        return report_obj.render(
            cr, uid, ids, 'repair_workorder.company_report',
            docargs, context=context)

    def printBarcode(self, cr, uid, value, width, height, context=None):
        try:
            width, height = int(width), int(height)
            barcode = createBarcodeDrawing(
                'EAN13', value=value, format='png', width=width, height=height)
            barcode = barcode.asString('png')
            barcode = barcode.encode('base64', 'strict')
        except (ValueError, AttributeError):
            raise exceptions.Warning(_('Cannot convert into barcode.'))

        return barcode
