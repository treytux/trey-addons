###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models

_QUALITY_PARTNER_LOG = [
    ('3_good', 'Good'),
    ('2_regular', 'Regular'),
    ('1_bad', 'Bad'),
]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    price_quality = fields.Selection(
        selection=_QUALITY_PARTNER_LOG,
        string='Value for money',
        default='2_regular',
        required=True,
    )
    service_quality = fields.Selection(
        selection=_QUALITY_PARTNER_LOG,
        string='Service',
        default='2_regular',
        required=True,
    )
    attencion_quality = fields.Selection(
        selection=_QUALITY_PARTNER_LOG,
        string='Attention given',
        default='2_regular',
        required=True,
    )
    qualification_log_ids = fields.One2many(
        comodel_name='quality.partner.log',
        inverse_name='partner_id',
    )
    partner_quality = fields.Integer(
        string='Partner quality',
    )
    qualification_date = fields.Date(
        string='Qualification date',
    )

    @api.onchange('price_quality', 'service_quality', 'attencion_quality')
    def onchange_quality(self):
        price = int(self.price_quality[0])
        service = int(self.service_quality[0])
        attencion = int(self.attencion_quality[0])
        self.partner_quality = price + service + attencion
        self.qualification_date = fields.Date.today()

    @api.multi
    def _prepare_qualification_log_vals(self):
        self.ensure_one()
        return {
            'partner_id': self.id,
            'price_quality': self.price_quality,
            'service_quality': self.service_quality,
            'attencion_quality': self.attencion_quality,
            'partner_quality': self.partner_quality,
            'qualification_date': self.qualification_date,
        }

    @api.multi
    def _update_qualification_log(self):
        Log = self.env['quality.partner.log']
        self.ensure_one()
        Log.create(self._prepare_qualification_log_vals())

    @api.multi
    def write(self, values):
        res = super().write(values)
        for partner in self:
            if 'price_quality' in values or \
                    'service_quality' in values or \
                    'attencion_quality' in values:
                partner._update_qualification_log()
        return res
