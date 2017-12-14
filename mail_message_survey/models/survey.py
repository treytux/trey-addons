# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields
import logging
_log = logging.getLogger(__name__)


class SurveyUserInput(models.Model):
    _name = 'survey.user_input'
    _inherit = ['survey.user_input', 'mail.thread', 'ir.needaction_mixin']

    state = fields.Selection(
        track_visibility='onchange')
