###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class EduFacility(models.Model):
    _name = 'edu.facility'
    _description = 'Facility'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
    )
    short_name = fields.Char(
        string='Short name',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        track_visibility='onchange',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id,
    )
