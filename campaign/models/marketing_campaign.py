# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, exceptions, _
import logging
_log = logging.getLogger(__name__)


class MarketingCampaign(models.Model):
    _inherit = 'marketing.campaign'

    @api.model
    def _get_users_group_salesman_manager(self):
        return [('groups_id', '=', self.env.ref(
            'campaign.group_campaign_salesman_manager').id)]

    @api.model
    def _get_users_group_media_manager(self):
        return [('groups_id', '=', self.env.ref(
            'campaign.group_campaign_media_manager').id)]

    @api.model
    def _get_users_group_campaign_manager(self):
        return [('groups_id', '=', self.env.ref(
            'campaign.group_campaign_manager').id)]

    @api.model
    def _get_users_group_campaign_survey_auditor(self):
        return [('groups_id', '=', self.env.ref(
            'campaign.group_campaign_survey_auditor').id)]

    @api.model
    def _get_users_group_campaign_media_auditor(self):
        return [('groups_id', '=', self.env.ref(
            'campaign.group_campaign_media_auditor').id)]

    @api.model
    def _get_object_id(self):
        ir_models = self.env['ir.model'].search([
            ('model', '=', 'marketing.campaign')])
        if not ir_models.exists():
            ir_models = self.env['ir.model'].search([])
        return ir_models[0]

    @api.model
    def _get_domain_survey_stage(self):
        stg_model, stg_id = self.env['ir.model.data'].get_object_reference(
            'survey', 'stage_in_progress')
        return [('stage_id', '=', stg_id)]

    city_ids = fields.Many2many(
        comodel_name='res.better.zip',
        relation='campaign2city_rel',
        column1='campaign_id',
        column2='city_id',
        readonly=True,
        states={'draft': [('readonly', False)],
                'visible': [('readonly', False)]})
    salesman_allowed_ids = fields.Many2many(
        comodel_name='res.users',
        compute='_compute_salesman_allowed',
        string='Salesmans allowed')
    salesman_ids = fields.Many2many(
        comodel_name='res.users',
        relation='campaign2salesman_rel',
        column1='campaign_id',
        column2='salesman_id',
        domain="[('id', 'in', salesman_allowed_ids[0][2])]",
        readonly=True,
        states={'draft': [('readonly', False)],
                'visible': [('readonly', False)],
                'running': [('readonly', False)]})
    # project_type = fields.Char(
    #     string='Project type')
    project_type_id = fields.Many2one(
        comodel_name='marketing.project_type',
        string='Project type')
    date_receipt = fields.Date(
        string='Date receipt',
        help="Date of receipt by the manager")
    date_done = fields.Date(
        string='Date done')
    survey_end_date = fields.Date(
        string='Survey end date')
    media_end_date = fields.Date(
        string='Media end date')
    business_survey_id = fields.Many2one(
        comodel_name='survey.survey',
        required=True,
        string='Business survey',
        domain=_get_domain_survey_stage)
    supplier_salesman_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesman supplier',
        required=True,
        domain=_get_users_group_salesman_manager)
    supplier_delivery_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Delivery supplier',
        required=True,
        domain=_get_users_group_media_manager)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Zone manager',
        domain=_get_users_group_campaign_manager,
        required=True)
    survey_audit_id = fields.Many2one(
        comodel_name='res.users',
        string='Survey audit',
        domain=_get_users_group_campaign_survey_auditor,
        required=True)
    media_audit_id = fields.Many2one(
        comodel_name='res.users',
        string='Media audit',
        domain=_get_users_group_campaign_media_auditor,
        required=True)
    media_deliveries_count = fields.Integer(
        compute='_compute_media_deliveries',
        string='Media deliveries count',
        store=False)
    dealer_allowed_ids = fields.Many2many(
        comodel_name='res.users',
        compute='_compute_dealer_allowed',
        string='Dealers allowed')
    dealer_ids = fields.Many2many(
        comodel_name='res.users',
        relation='campaign2dealer_rel',
        column1='campaign_id',
        column2='dealer_id',
        domain="[('id', 'in', dealer_allowed_ids[0][2])]",
        readonly=True,
        states={'draft': [('readonly', False)],
                'visible': [('readonly', False)],
                'running': [('readonly', False)]})
    container_type_ids = fields.Many2many(
        comodel_name='container.type',
        relation='campaign2container_type_rel',
        column1='campaign_id',
        column2='container_type_id')
    cube_type_ids = fields.Many2many(
        comodel_name='cube.type',
        relation='campaign2cube_type_rel',
        column1='campaign_id',
        column2='cube_type_id')
    collaboration_ids = fields.One2many(
        comodel_name='collaboration',
        inverse_name='campaign_id',
        string='Collaboration')
    trades_count = fields.Integer(
        compute='_compute_trades',
        string='Trades count',
        store=False)
    survey_user_inputs_done_count = fields.Integer(
        compute='_compute_survey_user_inputs_done',
        string='Survey user inputs done count',
        store=False)
    media_deliveries_requested_count = fields.Integer(
        compute='_compute_media_deliveries_requested',
        string='Media deliveries requested count',
        store=False)
    media_deliveries_delivered_count = fields.Integer(
        compute='_compute_media_deliveries_delivered',
        string='Media deliveries delivered count',
        store=False)
    collaborations_count = fields.Integer(
        compute='_compute_collaborations',
        string='Actions count',
        store=False)
    survey_cost = fields.Float(
        string='Survey cost')
    total_survey_cost = fields.Float(
        compute='_compute_total_survey_cost',
        string='Total survey cost',
        store=True,
        help="Calculated as survey cost * survey user inputs done.")
    delivery_cost = fields.Float(
        string='Delivery cost')
    total_delivery_cost = fields.Float(
        compute='_compute_total_delivery_cost',
        string='Total delivery cost',
        store=True,
        help="Calculated as delivery cost * media deliveries delivered count.")
    # Redefined to add default value
    object_id = fields.Many2one(
        default=_get_object_id)
    commercial_audit_percent = fields.Float(
        string='Commercial audit percent',
        help="Quality percentage of surveys audit")
    commercial_audit_file = fields.Binary(
        string='Commercial audit file')
    commercial_audit_filename = fields.Char(
        string='Commercial audit filename')
    media_audit_percent = fields.Float(
        string='Media audit percent',
        help="Quality percentage of medias audit")
    media_audit_file = fields.Binary(
        string='Media audit file')
    media_audit_filename = fields.Char(
        string='Media audit filename')
    # Related fields to display some fields in read-only to certain user groups
    name_readonly = fields.Char(
        string='Name',
        related='name')
    city_ids_readonly = fields.Many2many(
        string='Cities',
        related='city_ids')
    project_type_id_readonly = fields.Char(
        string='Project type',
        related='project_type_id.name')
    date_receipt_readonly = fields.Date(
        string='Date receipt',
        related='date_receipt')
    # Redefined to show translate values and add new state
    state = fields.Selection(
        selection=[
            ('draft', _('Expected')),
            ('visible', _('Started')),
            ('running', _('Surveys finished')),
            ('delivering', _('Deliveries started')),
            ('cancelled', _('Cancelled')),
            ('done', _('Finished'))],
        string='Status',
        copy=False)
    horeca = fields.Boolean(
        string='Horeca')

    @api.multi
    def write(self, vals):
        cr, uid, context = self.env.args
        user = self.env['res.users'].browse(uid)
        not_unlink_group_ids = [
            self.env.ref('campaign.group_campaign_manager').id,
            self.env.ref('campaign.group_campaign_salesman_manager').id,
            self.env.ref('campaign.group_campaign_media_manager').id]
        res = [g for g in user.groups_id.ids if g in not_unlink_group_ids]
        if (res and 'salesman_ids' in vals and
                len(vals['salesman_ids'][0][2]) < len(self.salesman_ids)):
            raise exceptions.Warning(_(
                'It is not allowed to remove any salesmans.'))
        if (res and 'dealer_ids' in vals and
                len(vals['dealer_ids'][0][2]) < len(self.dealer_ids)):
            raise exceptions.Warning(_(
                'It is not allowed to remove any dealers.'))
        return super(MarketingCampaign, self).write(vals)

    @api.one
    @api.depends('supplier_salesman_user_id')
    def _compute_salesman_allowed(self):
        domain = [
            ('partner_id.parent_id', '!=', False),
            ('partner_id.parent_id', '=',
                self.supplier_salesman_user_id.parent_id.id),
            ('groups_id', '=', self.env.ref(
                'campaign.group_campaign_salesman').id)]
        users = self.env['res.users'].search(domain)
        self.salesman_allowed_ids = users

    @api.one
    @api.depends('supplier_delivery_user_id')
    def _compute_dealer_allowed(self):
        domain = [
            ('partner_id.parent_id', '!=', False),
            ('partner_id.parent_id', '=',
                self.supplier_delivery_user_id.parent_id.id),
            ('groups_id', '=', self.env.ref(
                'campaign.group_campaign_dealer').id)]
        users = self.env['res.users'].search(domain)
        self.dealer_allowed_ids = users

    @api.one
    def _compute_media_deliveries(self):
        self.media_deliveries_count = len(self.env['media.delivery'].search([
            ('campaign_id', '=', self.id)]))

    @api.multi
    def _get_trades_domain(self):
        return [('zip_id', 'in', self.city_ids.ids), ('trade', '=', True)]

    @api.one
    def _compute_trades(self):
        self.trades_count = len(self.env['res.partner'].search(
            self._get_trades_domain()))

    @api.multi
    def _get_survey_user_inputs_done_domain(self):
        return [
            ('state', 'in', ('skip', 'pending_review', 'done', 'audited')),
            ('campaign_id', '=', self.id)]

    @api.one
    def _compute_survey_user_inputs_done(self):
        self.survey_user_inputs_done_count = len(
            self.env['survey.user_input'].search(
                self._get_survey_user_inputs_done_domain()))

    @api.multi
    def _get_media_deliveries_requested_domain(self):
        return [
            ('delivery_id.state', 'in', ('done', 'audited')),
            ('delivery_id.campaign_id', '=', self.id)]

    @api.one
    def _compute_media_deliveries_requested(self):
        delivery_lines = self.env['media.delivery.lines'].search(
            [('delivery_id.campaign_id', '=', self.id)])
        self.media_deliveries_requested_count = sum(
            [(line.requested) for line in delivery_lines])

    @api.multi
    def _get_media_deliveries_delivered_domain(self):
        return [
            ('delivery_id.state', 'in', ('done', 'audited')),
            ('delivery_id.campaign_id', '=', self.id)]

    @api.one
    def _compute_media_deliveries_delivered(self):
        delivery_lines = self.env['media.delivery.lines'].search(
            self._get_media_deliveries_delivered_domain())
        self.media_deliveries_delivered_count = sum(
            [(line.delivered) for line in delivery_lines])

    @api.one
    def _compute_collaborations(self):
        self.collaborations_count = len(self.env['collaboration'].search([
            ('campaign_id', '=', self.id)]))

    @api.one
    @api.depends('survey_cost', 'survey_user_inputs_done_count')
    def _compute_total_survey_cost(self):
        self.total_survey_cost = (
            self.survey_cost * self.survey_user_inputs_done_count)

    @api.one
    @api.depends('delivery_cost', 'media_deliveries_delivered_count')
    def _compute_total_delivery_cost(self):
        self.total_delivery_cost = (
            self.delivery_cost * self.media_deliveries_delivered_count)

    @api.multi
    def trades_tree_view(self):
        ctx = {
            'default_res_model': self._name,
            'default_res_id': self.id,
        }
        return {
            'name': _('Trades'),
            'domain': self._get_trades_domain(),
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': ctx.__str__()}

    @api.multi
    def state_visible_set(self):
        if not self.city_ids.exists():
            raise exceptions.Warning(_(
                'The campaign can not started, you must assign at least one '
                'zip code.'))
        self.state = 'visible'

    @api.multi
    def state_done_set(self):
        for collaboration in self.collaboration_ids:
            if collaboration.collaborate == 'no':
                continue
            if (collaboration.media_delivery_id.exists() and
                    collaboration.media_delivery_id.state != 'done'):
                raise exceptions.Warning(_(
                    'Media delivery of trade \'%s\' is not yet completed, you '
                    'must end it before finish the campaign.') %
                    (collaboration.trade_id.name))
            if (collaboration.survey_input_id.exists() and
                    collaboration.survey_input_id.state != 'done'):
                raise exceptions.Warning(_(
                    '\'%s\' survey user input of trade \'%s\' is not yet '
                    'completed, you must end it before finish the campaign.') %
                    (collaboration.survey_input_id.display_name,
                        collaboration.trade_id.name))
        return super(MarketingCampaign, self).state_done_set()

    @api.multi
    def state_running_set(self):
        '''Overwrite original function to avoid activities errors.'''
        self.state = 'running'
        self.survey_end_date = fields.Date.today()
        self.media_end_date = fields.Date.today()

    @api.multi
    def state_delivering_set(self):
        self.state = 'delivering'
