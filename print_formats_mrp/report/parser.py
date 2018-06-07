# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api
from functools import partial
import logging
_log = logging.getLogger(__name__)


class BOMStructureReport(models.TransientModel):
    _name = 'report.print_formats_mrp.report_pf_mrpbomstructure'

    @api.model
    def format_lang(self, value):
        return str('%.2f' % value).replace('.', ',')

    @api.multi
    def get_children(self, object, level=0):
        result = []

        def _get_rec(object, level):
            for l in object:
                res = {}
                res['product_id'] = l.product_id
                res['pname'] = l.product_id.name
                res['pcode'] = l.product_id.default_code
                res['pqty'] = l.product_qty
                res['uname'] = l.product_uom.name
                res['level'] = level
                res['code'] = l.bom_id.code
                result.append(res)
                if l.child_line_ids:
                    if level < 6:
                        level += 1
                    _get_rec(l.child_line_ids, level)
                    if level > 0 and level < 6:
                        level -= 1
            return result
        children = _get_rec(object, level)
        return children

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        bom_obj = self.env['mrp.bom']
        report = report_obj._get_report_from_name(
            'print_formats_mrp.report_pf_mrpbomstructure')
        selected_boms = bom_obj.browse(self.ids)

        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': selected_boms,
            'format_lang': partial(self.format_lang),
            'get_children': partial(self.get_children)}

        report = report_obj.browse(self.ids[0])
        return report.render(
            'print_formats_mrp.report_pf_mrpbomstructure', docargs)


class MRPOrderReport(models.TransientModel):
    _name = 'report.print_formats_mrp.report_pf_mrporder'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        production_obj = self.env['mrp.production']
        report = report_obj._get_report_from_name(
            'print_formats_mrp.report_pf_mrporder')
        productions = production_obj.browse(self.ids)

        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': productions}

        report = report_obj.browse(self.ids[0])
        return report.render(
            'print_formats_mrp.report_pf_mrporder', docargs)
