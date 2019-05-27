# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_rating = fields.Selection([
        ('1', 'Awful'),
        ('2', 'Very low'),
        ('3', 'Low'),
        ('4', 'Moderate'),
        ('5', 'High')],
        string='Rating')
