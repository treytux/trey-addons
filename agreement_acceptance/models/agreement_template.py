###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AgreementTemplate(models.Model):
    _name = 'agreement.template'
    _description = 'Agreement Template'

    name = fields.Char(
        string='Name',
        help='Document Name',
        required=True,
    )
    document = fields.Binary(
        string='Document',
        help='File that will contain the agreement',
        required=True,
    )
