# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class Booking(models.Model):
    _inherit = 'booking'

    methabook_id = fields.Integer(
        string='methabook Id')
    processed_ok = fields.Boolean(
        string='Processed',
        help='Processed correctly in Methabook')
    api_info = fields.Char(
        string='Api raw info',
        readonly=True)
    update_after_invoiced = fields.Boolean(
        string='Update After Invoice',
        copy=False,
        track_visibility='onchange')
    is_pay_tpv = fields.Boolean(
        string='Pay by TPV',
        track_visibility='onchange')
    date_tpv = fields.Date(
        string='Date TPV',
        track_visibility='onchange')
