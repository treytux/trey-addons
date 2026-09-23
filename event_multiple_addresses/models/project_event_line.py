###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class ProjectEventLine(models.Model):
    _inherit = 'project.event.line'

    @api.model
    def _get_default_address_ids(self):
        context = self.env.context
        model_name = context.get('active_model', False)
        active_id = context.get('active_id', False)
        if not model_name or not active_id:
            return False
        project = self.env[model_name].browse(active_id)
        return project.address_ids.ids

    address_id = fields.Many2one(
        string='Main location',
        domain="[('partner_category', '=', 'event_location')]",
    )
    address_ids = fields.Many2many(
        string='Extra locations',
        comodel_name='res.partner',
        relation='partner2project_event_line_rel',
        column1='project_event_line_id',
        column2='partner_id',
        domain="[('partner_category', '=', 'event_location')]",
        default=_get_default_address_ids,
    )

    def check_addresses(self, vals):
        if not self.address_id:
            return True
        event_obj = self.env['event.event']
        location_events = event_obj.search([
            ('date_begin', '<=', vals['date_end']),
            ('date_end', '>=', vals['date_begin']),
            '|', '|', '|',
            ('address_id', '=', vals['address_id']),
            ('address_ids', 'in', self.address_ids.ids),
            ('address_id', 'in', self.address_ids.ids),
            ('address_ids', 'in', vals['address_id']),
        ])
        if location_events:
            raise exceptions.ValidationError(_(
                'Location(s) already taken in another event/s (%s-%s).') % (
                    location_events.ids,
                    ', '.join(location_events.mapped('name'))))
        return True

    def generate_event_prepare(self, vals):
        self.ensure_one()
        vals['address_ids'] = [(6, 0, self.address_ids.ids)]
        return super().generate_event_prepare(vals)
