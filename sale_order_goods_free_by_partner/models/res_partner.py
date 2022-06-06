###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    goods_free_ids = fields.One2many(
        comodel_name='res.partner.goods_free',
        inverse_name='partner_id',
        string='Goods free',
    )
