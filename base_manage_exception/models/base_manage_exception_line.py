###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import date

from odoo import _, fields, models
from odoo.exceptions import UserError


class BaseExceptionLine(models.Model):
    _name = 'base.manage.exception.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Base manage exception lines'

    name = fields.Char(
        string='Name',
        required=True,
    )
    exception_id = fields.Many2one(
        comodel_name='base.manage.exception',
        string='Exception',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
    )
    user_ids = fields.Many2many(
        comodel_name='res.users',
        string='Users',
        relation='exception_line2user_rel',
        column1='exception_line_id',
        column2='user_id',
        required=True,
    )
    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model',
        required=True,
    )
    function_name = fields.Char(
        string='Function name',
        required=True,
        help='Name of the function to execute and from which its exceptions '
             'will be managed.'
    )
    function_params = fields.Char(
        string='Function params',
        default='{}',
        help='Parameters of the function which values are separator by comma. '
             'If the function has no parameters, leave empty.',
    )
    action_to_launch = fields.Selection(
        selection=[
            ('schedule_activity_exception', 'Schedule activity exception'),
        ],
        string='Action to launch',
        default='schedule_activity_exception',
        required=True,
        help='Action to execute when an exception error is detected in the '
             'selected function.',
    )
    notify_exception = fields.Boolean(
        string='Notify exception',
        default=True,
        help='If this option is disabled, exceptions will not be taken into '
             'account and the associated action will not be launched.'
    )

    def execute_action(self, action_to_launch, msg):
        if action_to_launch == 'schedule_activity_exception':
            activity_type = self.env.ref('mail.mail_activity_data_warning')
            mail_activity_obj = self.env['mail.activity']
            for user in self.user_ids:
                mail_activity_obj.create({
                    'activity_type_id': activity_type.id,
                    'res_id': self.id,
                    'summary': msg,
                    'user_id': user.id,
                    'res_model_id': self.env['ir.model']._get(self._name).id,
                    'date_deadline': date.today(),
                })
        else:
            raise UserError(_('Unknown action \'%s\'!') % action_to_launch)

    def run(self):
        model_obj = self.env[self.model_id.model]
        if hasattr(model_obj, self.function_name):
            fnc = getattr(model_obj, self.function_name)
            try:
                fnc(**eval(self.function_params))
            except Exception as e:
                if not self.notify_exception:
                    return
                msg_error = e and e.args and e.args[0] or e
                self.execute_action(self.action_to_launch, msg_error)
