# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
import base64
import StringIO
import unicodecsv as csv


class StockPickingDelivery(models.Model):
    _name = 'delivery.carrier.collect'
    _description = 'Delivery Carrier Collect'
    _order = 'id desc'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Code',
        default=lambda s: s.env['ir.sequence'].get('carrier.collect'),
        required=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('done', 'Done')],
        string='State',
        default='draft',
        readonly=True,
        track_visibility='onchange')
    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier')
    date_collect = fields.Datetime(
        string='Date Collect')
    picking_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='collect_id',
        string='Pickings')
    packages_total = fields.Float(
        compute='_compute_packages_total',
        string='Total packages')

    @api.one
    @api.depends('picking_ids')
    def _compute_packages_total(self):
        self.packages_total = sum([
            p.number_of_packages for p in self.picking_ids])

    @api.multi
    def name_get(self):
        def name(collect):
            return '[%s] %s' % (collect.name, collect.carrier_id.name or '')

        return [(r.id, name(r)) for r in self]

    @api.one
    def action_refresh(self):
        self.picking_ids = [(6, 0, [])]
        pickings = self.env['stock.picking'].search([
            ('collect_id', '=', False),
            ('carrier_id', '=', self.carrier_id.id)])
        self.picking_ids = [(6, 0, pickings.ids)]

    @api.one
    def action_done(self):
        if not self.picking_ids:
            raise exceptions.Warning(
                _('Error'), _('You must asign one or more pickings'))
        self.date_collect = fields.Datetime.now()
        self.state = 'done'
        return self.action_print()

    @api.one
    def action_to_draft(self):
        self.date_collect = None
        self.state = 'draft'

    @api.multi
    def action_print(self):
        report_name = 'stock_picking_delivery_form.carrier_collect'
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': dict(ids=self.ids)}

    @api.multi
    def _export_csv_lines_group_by_partner(self):
        self.ensure_one()
        partner_groups = {}
        priority = {
            s[0]: s[1]
            for s in self.env['stock.picking']._fields['priority'].selection}
        for pick in self.picking_ids:
            partner_groups.setdefault(pick.partner_id.id, []).append(pick)
        lines = []
        for pickings in partner_groups.values():
            pick = pickings[0]
            partner_name = pick.partner_id.name
            if pick.partner_id != pick.partner_id.root_partner_id:
                partner_name = '%s, %s' % (
                    pick.partner_id.root_partner_id.name, pick.partner_id.name)
            lines.append([
                self.name,
                self.date_collect,
                '%s' % partner_name,
                pick.partner_id.street or '',
                pick.partner_id.street2 or '',
                pick.partner_id.zip or '',
                pick.partner_id.city or '',
                pick.partner_id.state_id.name or '',
                pick.partner_id.mobile or '',
                pick.partner_id.phone or '',
                '%s-%s' % (pick.partner_id.id, self.name),
                pick.date_done or '',
                sum([p.number_of_packages for p in pickings]),
                priority[pick.priority],
                ', '.join([p.name for p in pickings if p.name])])
        return lines

    @api.multi
    def _export_csv_lines_no_group(self):
        self.ensure_one()
        lines = []
        priority = {
            s[0]: s[1]
            for s in self.env['stock.picking']._fields['priority'].selection}
        for pick in self.picking_ids:
            partner_name = pick.partner_id.name
            if pick.partner_id != pick.partner_id.root_partner_id:
                partner_name = '%s, %s' % (
                    pick.partner_id.root_partner_id.name, pick.partner_id.name)
            lines.append([
                self.name,
                self.date_collect,
                '%s' % partner_name,
                pick.partner_id.street or '',
                pick.partner_id.street2 or '',
                pick.partner_id.zip or '',
                pick.partner_id.city or '',
                pick.partner_id.state_id.name or '',
                pick.partner_id.mobile or '',
                pick.partner_id.phone or '',
                pick.name,
                pick.date_done or '',
                pick.number_of_packages,
                priority[pick.priority],
                ''])
        return lines

    @api.multi
    def action_export_csv(self):
        ofile = StringIO.StringIO()
        doc = csv.writer(
            ofile, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
        doc.writerow([
            'Collect Ref',
            'Collect Date',
            'Partner Name',
            'Street',
            'Street alternative',
            'Zip',
            'City',
            'State',
            'Mobile',
            'Phone',
            'Picking referece',
            'Picking date',
            'Number of packages',
            'Priority',
            'Notes'])
        if self.carrier_id.group_collect_by_partner:
            lines = self._export_csv_lines_group_by_partner()
        else:
            lines = self._export_csv_lines_no_group()
        for line in lines:
            doc.writerow(line)
        content = ofile.getvalue()
        content = base64.encodestring(content)
        wizard = self.env['delivery.carrier.collect_export_csv'].create({
            'file': content,
            'file_name': 'carrier_%s.csv' % self.name})
        return {
            'name': _('Export file'),
            'type': 'ir.actions.act_window',
            'res_model': 'delivery.carrier.collect_export_csv',
            'res_id': wizard.id,
            'view_type': 'form',
            'view_mode': 'form',
            'nodestroy': True,
            'target': 'new'}
