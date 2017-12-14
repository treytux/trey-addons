# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _, exceptions
import base64
import csv
import StringIO


class WizProductsPricelistReport(models.TransientModel):
    _name = 'wiz.product.pricelist.report'

    season_ids = fields.Many2many(
        comodel_name='product.season',
        relation='prod_tmpl_report_season_rel',
        column1='product_tmpl_rep_id',
        column2='season_id',
        string='Seasons')
    categ_ids = fields.Many2many(
        comodel_name='product.category',
        relation='product_categ_rel',
        column1='product_id',
        column2='categ_id',
        string='Product Categories')
    product_tmpl_ids = fields.Many2many(
        comodel_name='product.template',
        relation='wiz_product_id_rel',
        column1='wiz_product_id',
        column2='product_template_id',
        string='Templates to exclude')
    pricelist = fields.Many2one(
        comodel_name='product.pricelist',
        required=True,
        string='Pricelist')
    categ_id = fields.Many2one(
        comodel_name='product.category',
        string='Category')
    export_csv = fields.Boolean(
        string='Export to csv',
        help='Allow export to csv')
    file = fields.Binary(
        string='File',
        filter='*.csv',
        help='File to export')

    @api.multi
    def _get_file_name(self):
        self.file_name = _('products_pricelist_%s.csv') % fields.Datetime.now()

    file_name = fields.Char(
        string='File name',
        compute=_get_file_name)

    @api.multi
    def get_domain(self):
        domain = []
        season = self.season_ids
        product = self.product_tmpl_ids
        categ = self.categ_ids
        if season and categ:
            domain.append('|')
        if season:
            if len(season) == 1:
                domain.append(('season_id', '=', season.id))
            else:
                domain.append(('season_id', 'in', season.ids))
        if categ:
            if len(categ) == 1:
                domain.append(('categ_id', '=', categ.id))
            else:
                domain.append(('categ_id', 'in', categ.ids))
        if product:
            product_list = [product.id] if len(product) == 1 else product.ids
            domain.append(('id', 'not in', product_list))
        return domain

    @api.multi
    def get_pricelist(self, pricelist_id):
        return self.env['product.pricelist'].browse(pricelist_id)

    @api.multi
    def print_report(self):
        domain = self.get_domain()
        product = self.env['product.template'].search(domain)
        if not product and domain:
            raise exceptions.Warning(_('Select any filter'))
        if not self.export_csv:
            template = 'products_pricelist_report.products_pricelist_custom'
            return {'type': 'ir.actions.report.xml',
                    'report_name': template,
                    'datas': {'data': product.ids, 'ids': product.ids},
                    'context': {'report_name': template,
                                'pricelist': self.pricelist.id,
                                'ids': product.ids}}
        ofile = StringIO.StringIO()
        res = {}
        a = csv.writer(
            ofile, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
        for p in product:
            pp = p.product_variant_ids[0]
            price = pp.get_price_by_qty(self.pricelist.id)
            prices = price if price else p.list_price
            if prices != p.list_price:
                prices = ', '.join(list(set([pri for pri in prices])))
            description = p.description_sale and p.description_sale or ''
            row = [p.name, description, prices]
            encoded_row = [c.encode("utf-8") if isinstance(c, unicode) else c
                           for c in row]
            a.writerow(encoded_row)

        content = base64.encodestring(ofile.getvalue())
        self.write({'file': content})
        ofile.close()
        res = self.env['ir.model.data'].get_object_reference(
            'products_pricelist_report', 'wizard_wiz_export_pricelist_ok')
        return {'name': _('Export products pricelist'),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': [res and res[1] or False],
                'res_model': 'wiz.product.pricelist.report',
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new'}
