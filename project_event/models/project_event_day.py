###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectEventDay(models.Model):
    _name = 'project.event.day'
    _description = 'Days to generate event recurrency'

    sequence = fields.Integer()
    name = fields.Char()
