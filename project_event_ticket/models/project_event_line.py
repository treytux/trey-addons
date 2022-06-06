###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProjectEventTicket(models.Model):
    _inherit = 'project.event.line'

    def generate_event_ticket_line(self, line):
        return {
            'name': line.name,
            'product_id': line.product_id.id,
            'deadline': line.deadline,
            'seats_max': line.seats_max,
            'price': line.price,
        }

    def generate_event_prepare(self, vals):
        self.ensure_one()
        vals['event_ticket_ids'] = [
            (0, 0, self.generate_event_ticket_line(ln))
            for ln in self.project_id.event_ticket_ids
        ]
        return super().generate_event_prepare(vals)
