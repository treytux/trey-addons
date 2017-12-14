# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import api, models, fields
import logging
_log = logging.getLogger(__name__)


class Wiki(models.Model):
    _name = 'wiki'
    _description = 'Wiki'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Title',
        required=True)
    description = fields.Text(
        string='Description',
        translate=True)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        readonly=True,
        default=lambda self: self.env.user.id)
    tag_ids = fields.Many2many(
        string='Tags',
        comodel_name='wiki.tag',
        relation='wiki2tag_rel',
        column1='wiki_id',
        column2='tag_id')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('published', 'Published'),
            ('obsolete', 'Obsolete'),
            ('cancel', 'Cancel'),
        ],
        string='State',
        default='draft')

    @api.multi
    def to_draft(self):
        _log.info('to_draft')
        self.ensure_one()
        self.state = 'draft'

    @api.multi
    def to_published(self):
        _log.info('to_published')
        self.ensure_one()
        self.state = 'published'

    @api.multi
    def to_obsolete(self):
        _log.info('to_obsolete')
        self.ensure_one()
        self.state = 'obsolete'

    @api.multi
    def to_cancel(self):
        _log.info('to_cancel')
        self.ensure_one()
        self.state = 'cancel'
