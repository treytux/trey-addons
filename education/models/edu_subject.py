# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class EduSubject(models.Model):
    _name = 'edu.subject'
    _description = 'Subject'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        required=True)
    short_name = fields.Char(
        string='Short name')
    description = fields.Text(
        string='Description')
    active = fields.Boolean(
        string='Active',
        default=True,
        track_visibility='onchange')
