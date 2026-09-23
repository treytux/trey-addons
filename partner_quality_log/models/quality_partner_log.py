###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models

from .res_partner import _QUALITY_PARTNER_LOG


class QualityPartnerLog(models.Model):
    _name = 'quality.partner.log'
    _description = 'Quality Partner Log'
    _order = 'qualification_date desc'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
    )
    price_quality = fields.Selection(
        selection=_QUALITY_PARTNER_LOG,
        string='Value for money',
    )
    service_quality = fields.Selection(
        selection=_QUALITY_PARTNER_LOG,
        string='Service',
    )
    attencion_quality = fields.Selection(
        selection=_QUALITY_PARTNER_LOG,
        string='Attention given',
    )
    partner_quality = fields.Integer()
    qualification_date = fields.Date()
