# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, _, exceptions
import logging
_log = logging.getLogger(__name__)


class SurveyUserInputFinalize(models.TransientModel):
    _name = 'wiz.survey.user_input.finalize'
    _description = 'Finalize survey user inputs.'

    @api.multi
    def button_finalize(self):
        '''It finalizes the survey user inputs selected.'''
        # It check that the user belongs to any of the allowed groups.
        cr, uid, context = self.env.args
        user = self.env['res.users'].browse(uid)
        allow_group_ids = [
            self.env.ref('campaign.group_campaign_admin').id,
            self.env.ref('campaign.group_campaign_manager').id,
            self.env.ref('campaign.group_campaign_survey_auditor').id,
            self.env.ref('campaign.group_campaign_salesman_manager').id]
        res = [g for g in user.groups_id.ids if g in allow_group_ids]
        if not res:
            raise exceptions.Warning(_(
                'You are not authorized to complete survey user inputs.'))
        user_inputs = self.env['survey.user_input'].browse(
            self._context['active_ids'])
        for user_input in user_inputs:
            if user_input.state != 'pending_review':
                raise exceptions.Warning(_(
                    'The survey user inputs should be in \'Pending review\' '
                    'state.'))
            user_input.button_done()
        return {'type': 'ir.actions.act_window_close'}
