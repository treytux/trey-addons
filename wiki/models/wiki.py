###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, fields


class Wiki(models.Model):
    _name = 'wiki'
    _description = 'Wiki'
    _inherit = ['mail.thread', 'mail.activity.mixin']
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
            ('cancel', 'Cancel')],
        string='State',
        default='draft')

    @api.multi
    def to_draft(self):
        self.ensure_one()
        self.state = 'draft'

    @api.multi
    def to_published(self):
        self.ensure_one()
        self.state = 'published'

    @api.multi
    def to_obsolete(self):
        self.ensure_one()
        self.state = 'obsolete'

    @api.multi
    def to_cancel(self):
        self.ensure_one()
        self.state = 'cancel'
