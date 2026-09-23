###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError


class AcademyInvoiceActivitiesWizard(models.TransientModel):
    _name = 'academy.invoice.activities.wizard'
    _description = 'Wizard to invoice academy activities'

    name = fields.Char(
        string='Month & Year',
        required=True,
    )
    date = fields.Date(
        string='Invoice Date',
        default=fields.Date.context_today,
        required=True,
    )

    def create_invoices(self):
        self.ensure_one()
        invoice_obj = self.env['account.move']
        invoice_line_obj = self.env['account.move.line']
        context = self.env.context
        active_model = context.get('active_model', False)
        active_ids = context.get('active_ids', False)
        if active_model != 'academy.activity' or not active_ids:
            raise UserError(_('Please almost select an activity to invoice.'))
        activities = self.env['academy.activity'].browse(active_ids)
        partner_ids = {}
        inv_dates = self.date.replace(day=1) + relativedelta(months=1, days=-1)
        skip_states = ['pending_level', 'pending_group', 'cancelled']
        for activity in activities:
            if not activity.invoice_tutors:
                continue
            if not activity.product_id:
                raise ValidationError(_(
                    'Activity (%s) - %s without product.') % (
                        activity.id, activity.name))
            if activity.start_date and activity.start_date > self.date:
                raise ValidationError(_(
                    'Generation date must be top of the activity date'))
            if activity.end_date and activity.end_date < self.date:
                raise ValidationError(_(
                    'Generation date must be below end activity (%s) - %s') % (
                        activity.id, activity.name))
            for invoice in activity.invoice_ids:
                if (invoice.invoice_date.month == inv_dates.month
                        and invoice.invoice_date.year == inv_dates.year):
                    raise ValidationError(_(
                        'Invoices for these year and these month already '
                        'generated (%s) - %s') % (activity.id, activity.name))
            for enrollment in activity.enrollment_ids:
                if enrollment.state in skip_states:
                    continue
                if enrollment.partner_free_course:
                    continue
                enr_dates_start = enrollment.start_date.replace(day=1)
                enr_dates_end = (
                    enrollment.end_date.replace(day=1)
                    + relativedelta(months=1, days=-1)
                )
                if inv_dates < enr_dates_start or (
                        enr_dates_end and inv_dates > enr_dates_end):
                    continue
                partner = (
                    enrollment.tutor_ids and enrollment.tutor_ids[0]
                    or enrollment.student_id)
                if not partner.property_account_payable_id:
                    raise ValidationError(_(
                        'Partner without payable account %s') % (partner.name))
                if partner.id not in partner_ids:
                    vals_invoice = {
                        'partner_id': partner.id,
                        'invoice_date': self.date,
                        'move_type': 'out_invoice',
                        'enrollment_id': enrollment.id,
                        'activity_id': activity.id,
                        'invoice_user_id': self.env.user.id,
                    }
                    invoice_id = invoice_obj.create(vals_invoice).id
                    partner_ids[partner.id] = invoice_id
                else:
                    invoice_id = partner_ids[partner.id]
                product = activity.product_id
                product_category = product.categ_id
                if product.property_account_income_id:
                    product_account = (
                        product.property_account_income_id)
                elif (product_category
                        and product_category.property_account_income_categ_id):
                    product_account = (
                        product_category.property_account_income_categ_id)
                else:
                    raise ValidationError(_(
                        'Product of the activity (%s) - %s without account in '
                        'self or category.') % (activity.id, activity.name))
                price = (
                    enrollment.reduced_price and activity.activity_price_reduced
                    or activity.activity_price)
                name = (
                    self.name + ' - '
                    + activity.training_plan_id.name + ' - '
                    + activity.name + ' - ' + enrollment.student_id.name)
                analytic_account = (
                    activity.training_plan_id.analytic_account_id)
                vals_line = {
                    'name': name,
                    'analytic_distribution': {
                        analytic_account.id: 100,
                    },
                    'quantity': 1.0,
                    'price_unit': price,
                    'account_id': product_account.id,
                    'move_id': invoice_id,
                    'product_id': product.id,
                    'tax_ids': [(6, 0, [t.id for t in product.taxes_id])],
                }
                invoice_line_obj.create(vals_line)
        if not partner_ids:
            return {'type': 'ir.actions.act_window_close'}
        action = self.env['ir.actions.actions']._for_xml_id(
            'account.action_move_out_invoice_type')
        action.update({
            'domain': [('id', 'in', list(partner_ids.values()))],
            'view_mode': 'tree,form',
            'res_model': 'account.move',
        })
        return action
