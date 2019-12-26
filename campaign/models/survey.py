# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api
import logging
_log = logging.getLogger(__name__)


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    media_delivery_id = fields.Many2one(
        comodel_name='media.delivery',
        string='Media delivery')
    campaign_id = fields.Many2one(
        comodel_name='marketing.campaign',
        string='Campaign',
        required=True)
    # Para evitar que la nueva opcion del campo selection aparezca al final
    # (detras) de done, que no tiene sentido, redefino el campo entero.
    # state = fields.Selection(
    #     selection_add=[('pending_review', 'Pending review')])
    state = fields.Selection([
        ('new', 'Not started yet'),
        ('skip', 'Partially completed'),
        ('pending_review', 'Pending review'),
        ('done', 'Completed'),
        ('audited', 'Audited')])
    salesman_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesman',
        related='create_uid',
        readonly=True,
        store=True)
    date_write = fields.Datetime(
        string='Update date',
        related='write_date',
        readonly=True,
        store=True)

    @api.one
    def check_assign_survey_end_date_campaign(self):
        ''' If all survey user inputs are in 'done' state, assign current date
        to field 'survey_end_date' of campaign model.
        '''
        if self.campaign_id.business_survey_id.user_input_ids.exists():
            for uinput in self.campaign_id.business_survey_id.user_input_ids:
                if uinput.state != 'done':
                    break
                else:
                    self.campaign_id.survey_end_date = fields.Date.today()

    @api.multi
    def button_done(self):
        '''Change to 'Done' state and create or modify media delivery.'''
        media_delivery_obj = self.env['media.delivery']
        media_del_line_obj = self.env['media.delivery.lines']
        media_obj = self.env['media']
        collaboration_obj = self.env['collaboration']
        if not self.media_delivery_id.exists():
            exist_media_delivery = False
            supp_id = self.campaign_id.supplier_delivery_user_id.partner_id.id
            for line in self.user_input_line_ids:
                if line.question_id.media_type_id.exists():
                    # Crear la entrega de medios solo la primera vez
                    if not exist_media_delivery:
                        data = {
                            'supplier_delivery_id': supp_id,
                            'campaign_id': self.campaign_id.id,
                            'trade_id':
                                self.partner_id and self.partner_id.id or None}
                        media_delivery = media_delivery_obj.create(data)
                        exist_media_delivery = True
                        # Relacionar con la respuesta
                        self.media_delivery_id = media_delivery.id
                    # Crear un solo medio con las unidades indicadas
                    if (line.question_id.media_type_id.category == 'cube' and
                            int(line.value_number) > 0):
                        data_media = {
                            'name': line.question_id.media_type_id.name,
                            'type_id': line.question_id.media_type_id.id}
                        media = media_obj.create(data_media)
                        data_line = {
                            'delivery_id': media_delivery.id,
                            'media_id': media.id,
                            'requested': int(line.value_number)}
                        media_del_line_obj.create(data_line)
                    # Crear un medio por cada una de las unidades indicadas
                    else:
                        for m in range(1, int(line.value_number) + 1):
                            data_media = {
                                'name': line.question_id.media_type_id.name,
                                'type_id': line.question_id.media_type_id.id}
                            media = media_obj.create(data_media)
                            data_line = {
                                'delivery_id': media_delivery.id,
                                'media_id': media.id}
                            media_del_line_obj.create(data_line)
                    # Asignar la entrega de medios a la linea de colaboracion
                    # que corresponda con el comercio encuestado
                    collaborations = collaboration_obj.search([
                        ('campaign_id', '=', self.campaign_id.id),
                        ('trade_id', '=', self.partner_id.id)])
                    if collaborations.exists():
                        collaborations[0].sudo().write(
                            {'media_delivery_id': media_delivery.id})
        else:
            # Modificar entrega de medios: borrar todas las lineas y volver a
            # crearlas por si cambiase el tipo de medio de la pregunta ademas
            # de la respuesta
            [mline.unlink() for mline in self.media_delivery_id.media_lines]

            for line in self.user_input_line_ids:
                if line.question_id.media_type_id.exists():
                    # Crear un medio por cada una de las unidades indicadas
                    for m in range(1, int(line.value_number) + 1):
                        data_media = {
                            'name': line.question_id.media_type_id.name,
                            'type_id': line.question_id.media_type_id.id,
                        }
                        media = media_obj.create(data_media)
                        data_line = {
                            'delivery_id': self.media_delivery_id.id,
                            'media_id': media.id}
                        media_del_line_obj.create(data_line)
        self.state = 'done'
        self.check_assign_survey_end_date_campaign()

    @api.multi
    def button_skip(self):
        self.state = 'skip'

    @api.multi
    def button_pending_review(self):
        '''Change to 'Pending view' state.'''
        self.state = 'pending_review'

    @api.multi
    def button_audit(self):
        '''Change to 'Audited' state.'''
        self.state = 'audited'


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    media_type_id = fields.Many2one(
        comodel_name='media.type',
        string='Media type')
