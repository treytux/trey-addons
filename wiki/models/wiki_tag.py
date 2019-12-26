###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, fields


class WikiTag(models.Model):
    _name = 'wiki.tag'
    _description = 'Wiki tag'
    _order = 'id desc'

    name = fields.Char(
        string='Name',
        required=True)
    wiki_ids = fields.Many2many(
        string='Wiki',
        comodel_name='wiki',
        relation='wiki2tag_rel',
        column1='tag_id',
        column2='wiki_id')
    wiki_count = fields.Integer(
        string='Wiki entries',
        compute='_compute_wiki_count')

    @api.one
    def _compute_wiki_count(self):
        self.wiki_count = len(self.wiki_ids)
