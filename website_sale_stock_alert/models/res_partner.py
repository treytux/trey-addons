###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    alert_ids = fields.One2many(
        comodel_name='product.stock.alert',
        inverse_name='partner_id',
        string='Stock Alerts')
    stock_alerts_count = fields.Integer(
        compute='_compute_stock_alerts_count',
        string='Stock Alerts Count')

    @api.multi
    @api.depends('alert_ids')
    def _compute_stock_alerts_count(self):
        for partner in self:
            partner.stock_alerts_count = len(partner.alert_ids)
