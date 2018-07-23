# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'
    _order = 'order_id desc, id'

    order_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        related='order_id.partner_id')
    pos_order_date = fields.Datetime(
        comodel_name='pos.order',
        string='Pos order date',
        related='order_id.date_order')

    @api.multi
    def action_sale_and_pos_product_prices(self):
        sol_domain = [
            ('order_id', '!=', self.order_id.id),
            ('state', '!=', 'cancel'),
            ('product_id', '=', self.product_id.id)]
        if self.order_id.partner_id.exists():
            sol_domain.append(
                ('order_partner_id', '=', self.order_id.partner_id.id))
        sale_lines = self.env['sale.order.line'].search(
            sol_domain, order='create_date DESC')
        pos_line_domain = [
            ('order_id', '!=', self.order_id.id),
            ('product_id', '=', self.product_id.id)]
        if self.order_partner_id.exists():
            pos_line_domain.append(
                ('order_partner_id', '=', self.order_partner_id.id))
        pos_lines = self.env['pos.order.line'].search(
            pos_line_domain, order='create_date DESC')
        wizard = self.env['wiz.last.prices.from.sale.order.line'].create({
            'sale_order_line_ids': [(6, 0, sale_lines.ids)],
            'pos_order_line_ids': [(6, 0, pos_lines.ids)]})
        res = self.env['ir.model.data'].get_object_reference(
            'sale_order_last_prices_sale_and_pos',
            'wiz_last_prices_from_sale_order_line')
        res_id = res and res[1] or False
        return {
            'name': _('Last prices'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'wiz.last.prices.from.sale.order.line',
            'res_id': wizard.id,
            'type': 'ir.actions.act_window',
            'target': 'new'}
