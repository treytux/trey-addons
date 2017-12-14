# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_student = fields.Boolean(
        string='Student')
    is_teacher = fields.Boolean(
        string='Teacher')
    is_tutor = fields.Boolean(
        string='Tutor')
    tutor_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='student_tutor_rel',
        column1='student_id',
        column2='tutor_id',
        string='Tutors')
    student_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='student_tutor_rel',
        column1='tutor_id',
        column2='student_id',
        string='Students')

    @api.multi
    def create_user(self):
        self.ensure_one()
        group_ids = []
        if self.is_student:
            user = self.env.ref('education.template_student_user')
        if self.is_teacher:
            user = self.env.ref('education.template_teacher_user')
        if self.is_tutor:
            user = self.env.ref('education.template_tutor_user')
        if user:
            group_ids = [g.id for g in user.groups_id]
        user_vals = {
            'company_id': self.company_id.id,
            'name': self.name,
            'login': self.email or self.name,
            'password': self.email or self.name,
            'partner_id': self.id,
            'groups_id': [(6, 0, group_ids)]}
        self.env['res.users'].create(user_vals)
