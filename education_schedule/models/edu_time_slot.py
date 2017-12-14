# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class EduTimeSlot(models.Model):
    _name = 'edu.time.slot'
    _description = 'Time Slot'
    _inherit = ['mail.thread']
    _order = 'sequence, name'

    name = fields.Char(
        string='Name',
        required=True)
    start_time = fields.Float(
        string='Start Time')
    end_time = fields.Float(
        string='End Time')
    sequence = fields.Integer(
        string='Sequence')
    active = fields.Boolean(
        string='Active',
        default=True,
        track_visibility='onchange')
