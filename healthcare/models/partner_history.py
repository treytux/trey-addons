###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class PartnerHistory(models.Model):
    _name = 'partner.history'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Partner history'

    name = fields.Char(
        default=lambda self: _('Partner history'),
        translate=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner user',
        required=True,
        tracking=True,
    )
    date = fields.Datetime(
        string='Datetime',
        default=fields.Datetime.now,
        required=True,
        tracking=True,
    )
    location = fields.Char(
        string='Location',
        tracking=True,
    )
    type_id = fields.Many2one(
        comodel_name='partner.history.type',
        string='Type',
        required=True,
        tracking=True,
    )
    risk_ids = fields.Many2many(
        string='Risks',
        comodel_name='partner.risk',
        relation='risks2history_rel',
        column1='history_id',
        column2='risk_id',
        tracking=True,
    )
    note = fields.Html(
        string='Notes',
        tracking=True,
    )
    advancement = fields.Html(
        string='Advancement',
        tracking=True,
    )
    planning_in_actions = fields.Html(
        string='Planinng in actions',
        tracking=True,
    )
    family_notes = fields.Html(
        string='Family notes',
        tracking=True,
    )
    school_notes = fields.Html(
        string='School notes',
        tracking=True,
    )
