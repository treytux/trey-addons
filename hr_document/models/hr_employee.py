# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    document_ids = fields.One2many(
        string='Documents',
        comodel_name='ir.attachment',
        compute='_compute_document_ids',
        groups='base.group_hr_user',
    )
    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count',
        groups='base.group_hr_user',
    )

    @api.multi
    @api.depends('document_ids')
    def _compute_document_ids(self):
        for employee in self:
            employee.document_ids = self.env['ir.attachment'].search([
                ('res_model', '=', self._name), ('res_id', '=', employee.id)])

    @api.multi
    @api.depends('document_ids')
    def _compute_document_count(self):
        for employee in self:
            count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', employee.id),
            ]),
            employee.document_count = count and count[0] or 0

    @api.multi
    def action_attachment_view(self):
        action = self.env.ref('base.action_attachment').read()[0]
        action['context'] = {
            'default_res_model': self._name,
            'default_res_id': self.ids[0]
        }
        action['domain'] = ([
            ('res_model', '=', self._name), ('res_id', 'in', self.ids),
            ])
        return action
