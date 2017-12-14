# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import api, models, fields
import logging

_log = logging.getLogger(__name__)


class PortfolioTag(models.Model):
    _name = 'portfolio.tag'
    _description = 'Project Tag'

    name = fields.Char(
        string='Name',
        required=True)


class PortfolioProject(models.Model):
    _name = 'portfolio.project'
    _description = 'Project'

    @api.model
    def _get_user(self):
        cr, uid, context = self.env.args
        return uid

    name = fields.Char(
        string='Title',
        required=True)
    description = fields.Html(
        string='Description',
        translate=True,
        sanitize=False)
    content = fields.Html(
        string='Content',
        translate=True,
        sanitize=False)
    image = fields.Binary(
        string='Image')
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        readonly=True,
        default=_get_user)
    tag_ids = fields.Many2many(
        string='Tags',
        comodel_name='portfolio.tag',
        relation='project2tag_rel',
        column1='project_id',
        column2='tag_id')
