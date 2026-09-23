###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    expiry_docs_ids = fields.One2many(
        comodel_name='document.expiry',
        inverse_name='partner_id',
        string='Documentation',
    )
