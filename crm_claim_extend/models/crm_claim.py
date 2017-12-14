# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    order_ids = fields.One2many(
        comodel_name='sale.order',
        inverse_name='claim_id',
        string='Sale orders')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('progress', 'Progress'),
            ('pending_material', 'Pending material'),
            ('exception', 'Exception'),
            ('done', 'Done')],
        string='State',
        default='draft')

    @api.one
    def to_progress(self):
        assert self.state in ('draft', 'pending_material')
        self.state = 'progress'

    @api.one
    def to_pending_material(self):
        assert self.state == 'progress'
        self.state = 'pending_material'

    @api.one
    def to_exception(self):
        assert self.state == 'progress'
        self.state = 'exception'

    @api.one
    def to_done(self):
        assert self.state == 'progress'
        self.state = 'done'

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for claim in self:
            convert = self._fields['name'].convert_to_display_name
            result.append((
                claim.id, '[%s] %s' % (claim.code, convert(claim.name))))
        return result
