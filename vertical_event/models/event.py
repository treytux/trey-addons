###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    company_name = fields.Char(
        string='Company name',
        help='This field holds company name of attendee.',
    )
    company_charge = fields.Char(
        string='Company charge',
        help='This field holds company charge of attendee.',
    )
