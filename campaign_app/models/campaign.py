# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields
import logging
_log = logging.getLogger(__name__)


class CampaignApp(models.AbstractModel):
    _name = 'campaign.app'
    _description = 'Campaign App'

    @api.model
    def get_campaigns(self):
        env = self.env
        partner = env.user.partner_id

        res = []
        state = 'delivering' if partner.dealer else 'visible'
        campaigns = env['marketing.campaign'].search([
            ('state', '=', state),
            '|',
            ('salesman_ids', 'in', [env.user.id]),
            ('dealer_ids', 'in', [env.user.id])], order='id desc')
        if not campaigns.exists():
            _log.warning('get_campaigns: There is no active campaign.')
            return res
        return [{
            'id': c.id,
            'name': c.name,
            'horeca': c.horeca,
            'survey_id': (c.business_survey_id and
                          c.business_survey_id.id or False)
        } for c in campaigns] if campaigns else []

    @api.model
    def get_campaign_zips(self, campaign_id):
        env = self.env
        campaign = env['marketing.campaign'].browse(campaign_id)
        return [{
            'id': c.id,
            'name': c.name,
            'city': c.city,
            'code': c.code,
            'state_id': c.state_id.id,
            'state_name': c.state_id.name,
            'country_id': c.country_id.id,
            'country_name': c.country_id.name,
        } for c in campaign.city_ids] if campaign else []

    @api.model
    def get_trades(self, campaign_id):
        env = self.env
        partner = env.user.partner_id
        res = {'pending': [], 'progress': [], 'done': []}
        campaign = env['marketing.campaign'].browse(campaign_id)
        if not campaign.exists():
            _log.warning('get_trades: There is no campaign with id %s.'
                         % campaign_id)
            return res
        if partner.salesman and campaign.state != 'visible':
            _log.warning('get_trades: There is no visible campaign with id %s.'
                         % campaign_id)
            return res
        if partner.dealer and campaign.state != 'delivering':
            _log.warning(
                'get_trades: There is no delivering campaign with id %s.'
                % campaign_id)
            return res
        collaborations = env['collaboration'].search([
            ('campaign_id', '=', campaign_id)])
        col_trade_ids = []
        if collaborations.exists():
            for c in collaborations:
                col_trade_ids.append(c.trade_id.id)
                trade = {
                    'id': c.trade_id.id,
                    'name': c.trade_id.name,
                    'comercial': c.trade_id.comercial,
                    'is_company': c.trade_id.is_company,
                    'vat': c.trade_id.vat,
                    'display_name': c.trade_id.display_name,
                    'street': c.trade_id.street,
                    'zip': c.trade_id.zip,
                    'zip_id': c.trade_id.zip_id.id,
                    'city': c.trade_id.city,
                    'state': c.trade_id.state_id.name,
                    'country': c.trade_id.country_id.name,
                    'phone': c.trade_id.phone,
                    'mobile': c.trade_id.mobile,
                    'email': c.trade_id.email,
                    'image': c.trade_id.image_small,
                    'comment': c.trade_id.comment,
                    'activity': c.trade_id.activity,
                    'activity_others': c.trade_id.activity_others,
                    'name_surveyed': c.trade_id.name_surveyed,
                    'function_surveyed': c.trade_id.function_surveyed,
                    'opening_days': c.trade_id.opening_days,
                    'coordinates': c.trade_id.coordinates,
                    'category_id': c.trade_id.category_id and [
                        {'id': cat.id,
                         'name': cat.name,
                         'complete_name': cat.complete_name} for
                        cat in c.trade_id.category_id] or [],
                    'collaboration': {
                        'id': c.id,
                        'collaborate': c.collaborate,
                        'reason_id': c.reason_id.id if c.reason_id else None,
                        'reason': c.reason_id.name if c.reason_id else ''
                    },
                    'survey': False,
                    'survey_input_id': False,
                    'delivery': False,
                    'media_delivery_id': False
                }
                if partner.salesman:
                    trade['survey'] = (
                        False if not c.survey_input_id
                        else c.survey_input_id.state)
                    trade['survey_input_id'] = (
                        False if not c.survey_input_id
                        else c.survey_input_id.id)
                    if trade['collaboration']['collaborate'] == 'no':
                        res['done'].append(trade)
                    else:
                        if trade['survey'] in ['pending_review',
                                               'skip', 'done', 'audited']:
                            res['done'].append(trade)
                        elif not trade['survey'] or trade['survey'] in ['new']:
                            res['progress'].append(trade)
                elif partner.dealer:
                    trade['delivery'] = (
                        False if not c.media_delivery_id
                        else c.media_delivery_id.state)
                    trade['media_delivery_id'] = (
                        False if not c.media_delivery_id
                        else c.media_delivery_id.id)
                    if trade['collaboration']['collaborate'] == 'yes':
                        if trade['delivery'] in ['done', 'audited',
                                                 'pending_review']:
                            res['done'].append(trade)
                        else:
                            res['pending'].append(trade)
        if partner.salesman:
            domain = [('zip_id', 'in', campaign.city_ids.ids),
                      ('trade', '=', True),
                      ('id', 'not in', col_trade_ids)]
            trades = env['res.partner'].search(domain)
            if trades.exists():
                for t in trades:
                    trade = {
                        'id': t.id,
                        'name': t.name,
                        'comercial': t.comercial,
                        'is_company': t.is_company,
                        'vat': t.vat,
                        'display_name': t.display_name,
                        'street': t.street,
                        'zip': t.zip,
                        'city': t.city,
                        'state': t.state_id.name,
                        'country': t.country_id.name,
                        'phone': t.phone,
                        'mobile': t.mobile,
                        'email': t.email,
                        'image': t.image_small,
                        'comment': t.comment,
                        'activity': t.activity,
                        'activity_others': t.activity_others,
                        'name_surveyed': t.name_surveyed,
                        'function_surveyed': t.function_surveyed,
                        'opening_days': t.opening_days,
                        'category_id': [{
                            'id': cat.id,
                            'name': cat.name,
                            'complete_name': cat.complete_name}
                            for cat in t.category_id] if t.category_id else [],
                        'collaboration': False,
                        'survey': False,
                        'survey_input_id': False,
                        'delivery': False,
                        'media_delivery_id': False
                    }
                    res['pending'].append(trade)
        return res

    @api.model
    def get_survey(self, survey_id):
        env = self.env
        res = {}
        survey = env['survey.survey'].sudo().browse(survey_id)
        if not survey.exists():
            _log.warning('get_survey: There is no survey with id %s.'
                         % survey_id)
            return res
        return {
            'id': survey.id,
            'title': survey.title,
            'pages': [{
                'id': p.id,
                'title': p.title,
                'questions': [{
                    'id': q.id,
                    'question': q.question,
                    'type': q.type,
                    'mandatory': q.constr_mandatory,
                    'matrix_subtype': q.matrix_subtype,
                    'labels': [{
                        'id': l.id,
                        'value': l.value,
                        'quizz_mark': l.quizz_mark
                    } for l in q.labels_ids] if q.labels_ids else [],
                    'labels_2': [{
                        'id': l.id,
                        'value': l.value,
                        'quizz_mark': l.quizz_mark
                    } for l in q.labels_ids_2] if q.labels_ids_2 else [],
                } for q in p.question_ids] if p.question_ids else []
            } for p in survey.page_ids] if survey.page_ids else []}

    @api.model
    def get_media_delivery(self, media_delivery_id):
        env = self.env
        res = False
        media_delivery = env['media.delivery'].browse(media_delivery_id)
        if not media_delivery.exists():
            _log.warning(
                'get_media_delivery: There is no media_delivery with '
                'id %s.' % media_delivery_id)
            return res

        return {
            'id': media_delivery[0].id,
            'date_delivery': media_delivery[0].date_delivery,
            'state': media_delivery[0].state,
            'media_lines': ([{
                'id': l.id,
                'media': {
                    'id': l.media_id.id,
                    'name': l.media_id.name,
                    'type': l.media_type,
                    'address': l.media_id.address,
                    'coordinates': l.media_id.coordinates
                },
                'requested': l.requested,
                'delivered': l.delivered
            } for l in media_delivery[0].media_lines]
                if media_delivery[0].media_lines else [])
        }

    @api.model
    def write_media_delivery(self, media_delivery_data):
        env = self.env
        if 'date_delivery' in media_delivery_data and \
           not media_delivery_data['date_delivery']:
            media_delivery_data['date_delivery'] = fields.Date.today()
        if 'id' not in media_delivery_data:
            return {
                'errors': [{
                    'name': 'No se ha especificado id para Media delivery',
                    'value': 'No se ha especificado id para Media delivery'}]}
        media_delivery_id = media_delivery_data['id']
        del media_delivery_data['id']
        if 'media_lines' in media_delivery_data:
            media_delivery_lines = media_delivery_data['media_lines']
            del media_delivery_data['media_lines']
        media_delivery = env['media.delivery'].browse(media_delivery_id)
        if not media_delivery.exists():
            _log.warning(
                'get_media_delivery: There is no media_delivery '
                'with id %s.' % media_delivery_id)
            return {'errors': [{
                'name': 'Media delivery no existe',
                'value': 'Media delivery con id %s no '
                         'existe' % media_delivery_id}]}
        media_delivery_data['state'] = (
            'pending_review'
            if media_delivery_data['state'] == 'pending_delivery'
            else media_delivery_data['state'])
        media_delivery.write(media_delivery_data)
        for l in media_delivery_lines:
            media_delivery_line = env['media.delivery.lines'].browse(
                l['id'])
            if not media_delivery_line.exists():
                return {'errors': [{
                    'name': 'Media delivery line no existe',
                    'value': 'Media delivery line con '
                             'id %s no existe' % l.id}]}
            media_delivery_line.write({'delivered': int(l['delivered'])})
        return True

    @api.model
    def get_user_input(self, survey_input_id, user_input=None):
        env = self.env
        res = False
        if user_input is None:
            user_input = env['survey.user_input'].browse(survey_input_id)
        if not user_input.exists():
            _log.warning(
                'get_user_input: There is no user_input for '
                'survey_input_id %s.' % (survey_input_id))
            return res

        data = {}
        for l in user_input[0].user_input_line_ids:
            if l.question_id.id not in data.keys():
                data[l.question_id.id] = {
                    'id': l.id,
                    'skipped': l.skipped,
                    'answer_type': l.answer_type,
                    'value_text': l.value_text,
                    'value_number': l.value_number,
                    'value_date': l.value_date,
                    'value_free_text': l.value_free_text,
                    'value_suggested': [{
                        'id': vs.id,
                        'value': vs.value,
                    } for vs in l.value_suggested]
                    if l.value_suggested else [],
                    'value_suggested_row': [{
                        'id': vsr.id,
                        'value': vsr.value,
                    } for vsr in l.value_suggested_row]
                    if l.value_suggested_row else [],
                }
            else:
                data[l.question_id.id]['value_suggested'].extend([{
                    'id': vs.id,
                    'value': vs.value} for vs in l.value_suggested]
                    if l.value_suggested else [])
                data[l.question_id.id]['value_suggested_row'].extend([{
                    'id': vsr.id,
                    'value': vsr.value} for vsr in l.value_suggested_row]
                    if l.value_suggested_row else [])
        return {
            'id': user_input[0].id,
            'state': user_input[0].state,
            'user_input_line_ids': data}

    @api.model
    def create_user_input(self, campaign_id, collaboration_id, survey_id,
                          partner_id, lines, close=False):
        env = self.env
        try:
            user_input = env['survey.user_input'].create({
                'campaign_id': campaign_id,
                'survey_id': survey_id,
                'partner_id': partner_id,
            })
            for l in lines:
                user_input_lines = []
                for i in l['inputs']:
                    data = {
                        'survey_id': survey_id,
                        'user_input_id': user_input.id,
                        'question_id': int(l['question_id']),
                        'skipped': True,
                    }
                    if l['skipped'] is False:
                        data['skipped'] = False
                        data['answer_type'] = l['answer_type']
                        data['value_text'] = (
                            i['value'] if l['answer_type'] == 'text' else None)
                        data['value_suggested'] = (
                            int(i['value'])
                            if l['answer_type'] == 'suggestion' else None)
                        data['value_number'] = (
                            float(i['value'])
                            if l['answer_type'] == 'number' and
                            i['value'] != '' else None)
                        data['value_date'] = (
                            i['value'] if l['answer_type'] == 'date' and
                            i['value'] != '' else None)
                        data['value_free_text'] = (
                            i['value'] if l['answer_type'] == 'free_text'
                            else None)
                        data = {
                            k: v for k, v in data.iteritems() if v is not None}
                    user_input_lines.append(data)
                for l in user_input_lines:
                    env['survey.user_input_line'].create(l)
            if close is True:
                user_input.button_pending_review()
            else:
                user_input.button_skip()
            collaboration = env['collaboration'].browse(collaboration_id)
            if collaboration:
                collaboration.write({'survey_input_id': user_input.id})

            return self.get_user_input(user_input.id, user_input)
        except Exception as e:
            return {'errors': [{'name': e[0], 'value': e[1]}]}

    @api.model
    def write_user_input(self, user_input_id, lines, close=False):
        env = self.env
        try:
            for l in lines:
                if 'answer_id' in l and l['skipped'] is False:
                    user_input_line = env['survey.user_input_line'].browse(
                        l['answer_id'])
                    if user_input_line.exists():
                        data = {
                            'answer_type': l['answer_type'],
                            'skipped': False}
                        if l['answer_type'] == 'number':
                            data['value_number'] = l['inputs'][0]['value']
                        if l['answer_type'] == 'free_text':
                            data['value_free_text'] = l['inputs'][0]['value']
                        if l['answer_type'] == 'text':
                            data['value_text'] = l['inputs'][0]['value']
                        if l['answer_type'] == 'date':
                            data['value_date'] = l['inputs'][0]['value']
                        if l['answer_type'] == 'suggestion':
                            data['value_suggested'] = l['inputs'][0]['value']
                        user_input_line.write(data)
                else:
                    user_input_lines = env['survey.user_input_line'].search([
                        ('user_input_id', '=', user_input_id),
                        ('question_id', '=', l['question_id'])])
                    user_input_lines.unlink()
                    if l['skipped'] is False:
                        for v in l['inputs']:
                            data = {
                                'user_input_id': user_input_id,
                                'question_id': l['question_id'],
                                'answer_type': l['answer_type'],
                                'value_suggested': v['value'],
                                'quizz_mark': v['quizz_mark'],
                                'skipped': False
                            }
                            env['survey.user_input_line'].create(data)
                    else:
                        data = {
                            'user_input_id': user_input_id,
                            'question_id': l['question_id'],
                            'answer_type': None,
                            'skipped': True
                        }
                        env['survey.user_input_line'].create(data)
            user_input = env['survey.user_input'].browse(user_input_id)
            if user_input.exists():
                if close is True:
                    user_input.button_pending_review()
                else:
                    user_input.button_skip()

            return self.get_user_input(user_input_id)
        except Exception as e:
            return {'errors': [{'name': e[0], 'value': e[1]}]}

    @api.model
    def create_collaboration(self, collaboration_data):
        env = self.env
        try:
            collaboration = env['collaboration'].create(
                collaboration_data)
            return {
                'id': collaboration.id,
                'collaborate': collaboration.collaborate,
                'reason_id': (collaboration.reason_id.id if
                              collaboration.reason_id else None),
                'reason': (collaboration.reason_id.name if
                           collaboration.reason_id else '')}
        except Exception as e:
            return {'errors': [
                {'name': 'Error al crear Colaboración', 'value': e.message}]}

    @api.model
    def write_collaboration(self, collaboration_data):
        env = self.env
        collaboration_id = collaboration_data['id']
        del collaboration_data['id']
        collaboration = env['collaboration'].browse(collaboration_id)
        if collaboration:
            collaboration.write(collaboration_data)
            return {
                'id': collaboration.id,
                'collaborate': collaboration.collaborate,
                'reason_id': (collaboration.reason_id.id if
                              collaboration.reason_id else None),
                'reason': (collaboration.reason_id.name if
                           collaboration.reason_id else '')}
        else:
            return {'errors': [{
                'name': 'Colaboración no existe',
                'value': 'La colaboración con id %s no existe' % (
                    collaboration_id)}]}
