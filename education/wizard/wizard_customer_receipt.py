# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields


class EduWizardCustomerReceipt(models.TransientModel):
    _name = 'edu.wizard.customer.receipt'
    _description = 'Wizard Customer Receipt'

    training_plan_id = fields.Many2one(
        comodel_name='edu.training.plan',
        string='Training Plan',
        required=True)
    classroom_id = fields.Many2one(
        comodel_name='edu.training.plan.classroom',
        string='Classroom',
        required=True,
        domain="[('training_plan_id','=',training_plan_id)]")
    receipt_description = fields.Char(
        string='Description',
        required=True)
    receipt_amount = fields.Float(
        string='Amount',
        required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id)
    bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        string='Bank',
        domain="[('company_id','=',company_id)]",
        required=True)

    @api.model
    def default_get(self, fields):
        res = super(EduWizardCustomerReceipt, self).default_get(fields)
        context = self.env.context
        if context.get('active_model') == 'edu.training.plan.classroom':
            classroom = self.env['edu.training.plan.classroom'].browse(
                context['active_id'])
            res.update({
                'classroom_id': classroom.id,
                'training_plan_id': classroom.training_plan_id.id})
        return res

    @api.multi
    def button_print_report_receipt(self):
        report_name = 'education.receipt'
        data = self.read()[0]
        context = self.env.context
        if context.get('active_model') == 'edu.training.plan.classroom':
            classroom = self.env['edu.training.plan.classroom'].browse(
                context.get('active_id'))
            student_ids = [e.id for e in classroom.student_ids]
            data['active_ids'] = student_ids
        else:
            data['active_ids'] = context.get('active_ids')
        return self.env['report'].get_action(self, report_name, data=data)
