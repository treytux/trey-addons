###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    last_order_date = fields.Datetime(
        string='Last order date',
        store=True,
        compute='_compute_last_order_date',
    )
    average_time = fields.Float(
        string='Average time between orders',
        default=0.0,
        store=True,
        compute='_compute_average_time',
    )

    @api.multi
    @api.depends('sale_order_ids.confirmation_date')
    def _compute_last_order_date(self):
        for partner in self:
            domain = [
                ('partner_id', '=', partner.id),
                ('state', 'in', ['sale', 'done']),
            ]
            last_order = partner.env['sale.order'].search(
                domain, order='confirmation_date desc', limit=1)
            if last_order:
                partner.last_order_date = last_order.confirmation_date

    @api.multi
    @api.depends('sale_order_ids.confirmation_date')
    def _compute_average_time(self):
        for partner in self:
            domain = [
                ('partner_id', '=', partner.id),
                ('state', 'in', ['sale', 'done']),
            ]
            orders = partner.env['sale.order'].search_count(domain)
            if orders <= 1:
                continue
            first_order = partner.env['sale.order'].search(
                domain, order='confirmation_date asc', limit=1)
            last_order = partner.env['sale.order'].search(
                domain, order='confirmation_date desc', limit=1)
            first_date = first_order.confirmation_date
            last_date = last_order.confirmation_date
            partner.average_time = (last_date - first_date).days / orders
