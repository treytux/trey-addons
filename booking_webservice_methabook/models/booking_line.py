# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class BookingLine(models.Model):
    _inherit = 'booking.line'

    methabook_id = fields.Integer(
        string='methabook Id')
    cost_gross = fields.Float(
        string='Cost Gross',
        track_visibility='onchange')
    service_country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country')
    update_after_invoiced = fields.Boolean(
        string='Update After Invoice',
        copy=False,
        track_visibility='onchange')
