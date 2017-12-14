# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class EduPeriod(models.Model):
    _name = 'edu.period'
    _description = 'Period'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        required=True)
    start_date = fields.Date(
        string='Start Date',
        required=True)
    end_date = fields.Date(
        string='End Date')
    active = fields.Boolean(
        string='Active',
        default=True,
        track_visibility='onchange')
