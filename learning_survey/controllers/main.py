# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import http
from openerp.http import request
from openerp import fields
import logging
import openerp.addons.survey.controllers.main as main
import random
_log = logging.getLogger(__name__)


class WebsiteSurvey(main.WebsiteSurvey):

    def get_partner_company(self):
        user = request.env.user
        if user.partner_id.is_company:
            return user.partner_id
        else:
            partner = user.partner_id
            if partner.parent_id:
                while partner.parent_id:
                    partner = partner.parent_id
                    if partner.is_company:
                        return partner
            else:
                return partner
        return None

    # Survey start
    @http.route(['/survey/start/<model("survey.survey"):survey>',
                 '/survey/start/<model("survey.survey"):survey>/<string:'
                 'token>'],
                type='http', auth='public', website=True)
    def start_survey(self, survey, token=None, **post):
        env = request.env
        user_input_obj = env['survey.user_input']
        subscription_obj = env['learning.subscription']

        # Test mode
        if token and token == 'phantom':
            _log.info('[survey] Phantom mode')
            user_input = user_input_obj.create({
                'survey_id': survey.id,
                'test_entry': True})
            return request.website.render('survey.survey_init', {
                'survey': survey,
                'page': None,
                'token': user_input.token})

        # END Test mode
        partner = self.get_partner_company()
        if partner:
            subscriptions = subscription_obj.search([
                ('partner_id', '=', partner.id),
                ('training_id.exam_id.survey_id', '=', survey.id),
                ('date_end', '>=', fields.Datetime.now())])
            if subscriptions:
                user_input = user_input_obj.search([
                    ('partner_id', '=', partner.id),
                    ('subscription_id', '=', subscriptions[0].id),
                    ('state', '!=', 'done')])
                # Si tengo encuesta rellena que no este done, devuelvo
                # esta, si no la tengo, creo una nueva y devuelvo la url
                if not user_input:
                    if subscriptions[0].approved or \
                       subscriptions[0].exam_attempts <= 0:
                        return request.website.render(
                            'survey.not_exam_attempts',
                            {'subscription': subscriptions[0]})
                    user_input = user_input_obj.create({
                        'survey_id': survey.id,
                        'partner_id': partner.id,
                        'subscription_id': subscriptions[0].id})
                    self.generate_random_pages(
                        survey=survey,
                        subscription=subscriptions[0],
                        user_input_id=user_input)
                else:
                    user_input = user_input[0]

                if user_input.state == 'new':  # Intro page
                    subscriptions[0].write({
                        'exam_attempts': subscriptions[0].exam_attempts - 1})
                    return request.website.render(
                        'survey.survey_init',
                        {
                            'survey': survey,
                            'page': None,
                            'token': user_input.token})
                else:
                    return request.redirect('/survey/fill/%s/%s' % (
                        survey.id, user_input.token))
            return request.website.render("website.403")

    def generate_random_pages(self, survey, subscription, user_input_id):
        """
        Metodo para seleccionar las preguntas de forma aleatoria y
        asignarlas a user_input

        :param survey_id: Encuesta
        :param subscription_id: Subscripcion

        :return: Estado de la creacion de las lineas
        """
        env = request.env
        number_questions = subscription.training_id.exam_id.number_questions
        page_ids = survey.page_ids.ids
        random.shuffle(page_ids)
        for page_id in page_ids[:number_questions]:
            data = {
                'user_input_id': user_input_id.id,
                'survey_id': survey.id,
                'page_id': page_id,
            }
            env['survey.user_input.page'].sudo().create(data)

    # Survey displaying
    @http.route(['/survey/fill/<model("survey.survey"):survey>/<string:token>',
                 '/survey/fill/<model("survey.survey"):survey>/<string:'
                 'token>/<string:prev>'],
                type='http', auth='public', website=True)
    def fill_survey(self, survey, token, prev=None, **post):
        env = request.env
        res = super(WebsiteSurvey, self).fill_survey(
            survey=survey, token=token, prev=prev)
        subscription_obj = env['learning.subscription']
        user_input_obj = env['survey.user_input']

        # Load the user_input
        user_input = user_input_obj.search([('token', '=', token)])
        if not user_input:
            return request.website.render("website.403")
        user_input = user_input[0]
        # Aqui comprobamos el estado del examen y ponemos los intentos a 0
        if user_input.state == 'done':  # Display success message
            if user_input.approved:
                subscription_obj.sudo().write({'exam_attempts': 0})
            return request.website.render(
                'learning_survey.sfinished',
                {'survey': survey, 'token': token, 'user_input': user_input})
        res.qcontext['user_input'] = user_input
        return res

    @http.route(['/survey/print/<model("survey.survey"):survey>',
                 '/survey/print/<model("survey.survey"):survey>'
                 '/<string:token>'],
                type='http', auth='public', website=True)
    def print_survey(self, survey, token=None, **post):
        env = request.env
        # Load the user_input
        user_input = env['survey.user_input'].sudo().search(
            [('token', '=', token)])
        if not user_input:
            return request.website.render("website.403")
        user_input = user_input[0]
        return request.website.render(
            'survey.survey_print',
            {'survey': survey,
             'token': token,
             'page_nr': 0,
             'user_input': user_input,
             'quizz_correction': True if survey.quizz_mode and token else False
             })
