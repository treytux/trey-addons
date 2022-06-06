###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, fields, models


class ProjectEventLine(models.Model):
    _inherit = 'project.event.line'

    address_id = fields.Many2one(
        string='Main location',
        domain="[('event_location', '=', True)]",
    )
    address_ids = fields.Many2many(
        string='Extra locations',
        comodel_name='res.partner',
        relation='partner2project_event_line_rel',
        column1='project_event_line_id',
        column2='partner_id',
        domain="[('event_location', '=', True)]",
    )

    def generate_event_prepare(self, vals):
        self.ensure_one()
        vals['address_ids'] = [(6, 0, self.address_ids.ids)]
        if not self.address_id:
            return super().generate_event_prepare(vals)
        event_obj = self.env['event.event']
        location_events = event_obj.search([
            ('date_begin', '<=', vals['date_end']),
            ('date_end', '>=', vals['date_begin']),
            '|',
            ('address_id', '=', vals['address_id']),
            ('address_ids', 'in', self.address_ids.ids),
        ])
        if location_events:
            raise exceptions.ValidationError(_(
                'Location(s) already taken in another event.'))
        return super().generate_event_prepare(vals)
