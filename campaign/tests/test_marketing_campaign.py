# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp.tests.common import TransactionCase
import logging
_log = logging.getLogger(__name__)


class MarketingCampaignCase(TransactionCase):
    '''Test ``marketing.campaign`` when...'''

    def create_users(self):
        '''Create one user for each security group.'''
        partner_obj = self.env['res.partner']
        user_obj = self.env['res.users']

        # Campaign admin
        partner_data = {
            'name': 'Admin test 1',
            'company_id': self.ref('base.main_company'),
            'customer': False}
        self.partner_admin = partner_obj.create(partner_data)
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_manager'),
            self.ref('campaign.group_campaign_admin')]
        user_data = {
            'partner_id': self.partner_admin.id,
            'login': 'admin_test1@domain.es',
            'password': '123',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]}
        self.user_admin = user_obj.create(user_data)

        # Campaign manager
        partner_data = {
            'name': 'Manager test 1',
            'company_id': self.ref('base.main_company'),
            'customer': False}
        self.partner_manager = partner_obj.create(partner_data)
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_manager'),
            self.ref('campaign.group_campaign_manager')]
        user_data = {
            'partner_id': self.partner_manager.id,
            'login': 'manager_test1@domain.es',
            'password': '123',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]}
        self.user_manager = user_obj.create(user_data)

        # Campaign salesman manager
        partner_data = {
            'name': 'Salesman manager test 1',
            'company_id': self.ref('base.main_company'),
            'customer': False}
        self.partner_salesman_manager = partner_obj.create(partner_data)
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_user'),
            self.ref('campaign.group_campaign_salesman_manager')]
        user_data = {
            'partner_id': self.partner_salesman_manager.id,
            'login': 'salesman_manager_test1@domain.es',
            'password': '123',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]}
        self.user_salesman_manager = user_obj.create(user_data)

        # Campaign media manager
        partner_data = {
            'name': 'Media manager test 1',
            'company_id': self.ref('base.main_company'),
            'customer': False}
        self.partner_media_manager = partner_obj.create(partner_data)
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_user'),
            self.ref('campaign.group_campaign_media_manager')]
        user_data = {
            'partner_id': self.partner_media_manager.id,
            'login': 'media_manager_test1@domain.es',
            'password': '123',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]}
        self.user_media_manager = user_obj.create(user_data)

        # Campaign survey auditor
        partner_data = {
            'name': 'Survey auditor test 1',
            'company_id': self.ref('base.main_company'),
            'customer': False}
        self.partner_survey_auditor = partner_obj.create(partner_data)
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_user'),
            self.ref('campaign.group_campaign_survey_auditor')]
        user_data = {
            'partner_id': self.partner_survey_auditor.id,
            'login': 'survey_auditor_test1@domain.es',
            'password': '123',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]}
        self.user_survey_auditor = user_obj.create(user_data)

        # Campaign media auditor
        partner_data = {
            'name': 'Media auditor test 1',
            'company_id': self.ref('base.main_company'),
            'customer': False}
        self.partner_media_auditor = partner_obj.create(partner_data)
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_user'),
            self.ref('campaign.group_campaign_media_auditor')]
        user_data = {
            'partner_id': self.partner_media_auditor.id,
            'login': 'media_auditor_test1@domain.es',
            'password': '123',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]}
        self.user_media_auditor = user_obj.create(user_data)

        # Campaign salesman
        partner_data = {
            'name': 'Salesman test 1',
            'company_id': self.ref('base.main_company'),
            'customer': False}
        self.partner_salesman = partner_obj.create(partner_data)
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_user'),
            self.ref('campaign.group_campaign_salesman')]
        user_data = {
            'partner_id': self.partner_salesman.id,
            'login': 'salesman_test1@domain.es',
            'password': '123',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]}
        self.user_salesman = user_obj.create(user_data)

        # Campaign dealer
        partner_data = {
            'name': 'Dealer test 1',
            'company_id': self.ref('base.main_company'),
            'customer': False}
        self.partner_dealer = partner_obj.create(partner_data)
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_user'),
            self.ref('campaign.group_campaign_dealer')]
        user_data = {
            'partner_id': self.partner_dealer.id,
            'login': 'dealer_test1@domain.es',
            'password': '123',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]}
        self.user_dealer = user_obj.create(user_data)

    def create_product(self):
        product_obj = self.env['product.product']
        data = {'name': 'Product test'}
        return product_obj.create(data)

    def create_survey(self, name):
        survey_obj = self.env['survey.survey']
        data = {'title': name}
        return survey_obj.create(data)

    def create_page(self, name, survey):
        page_obj = self.env['survey.page']
        data = {
            'title': name,
            'survey_id': survey.id}
        return page_obj.create(data)

    def create_question(self, name, survey, page, media_type=None):
        question_obj = self.env['survey.question']
        data = {
            'question': name,
            'type': 'numerical_box',
            'survey_id': survey.id,
            'page_id': page.id}
        if media_type is not None:
            data.update({'media_type_id': media_type.id})
        return question_obj.create(data)

    def create_user_input(self, survey, campaign, media_delivery=None):
        user_input_obj = self.env['survey.user_input']
        data = {
            'survey_id': survey.id,
            'campaign_id': campaign.id}
        if media_delivery is not None:
            data.update({'media_delivery_id': media_delivery.id})
        return user_input_obj.create(data)

    def create_user_input_line(
            self, survey, question, user_input, value_number):
        line_input_obj = self.env['survey.user_input_line']
        data = {
            'answer_type': 'number',
            'survey_id': survey.id,
            'question_id': question.id,
            'user_input_id': user_input.id,
            'value_number': value_number}
        return line_input_obj.create(data)

    def create_campaign(self, name, survey):
        campaign_obj = self.env['marketing.campaign']
        data = {
            'name': name,
            'supplier_salesman_user_id': self.user_salesman_manager.id,
            'supplier_delivery_user_id': self.user_media_manager.id,
            'user_id': self.user_manager.id,
            'survey_audit_id': self.user_survey_auditor.id,
            'media_audit_id': self.user_media_auditor.id,
            'business_survey_id': survey.id}
        return campaign_obj.create(data)

    def create_media_delivery(self, campaign):
        media_delivery_obj = self.env['media.delivery']
        data = {
            'supplier_delivery_id':
                campaign.supplier_delivery_user_id.partner_id.id,
            'campaign_id': campaign.id}
        return media_delivery_obj.create(data)

    def create_media_type(self, name, product, category):
        media_type_obj = self.env['media.type']
        data = {
            'name': name,
            'product_id': product.id,
            'category': category}
        return media_type_obj.create(data)

# def setUp(self):
#     '''Create marketing campaign, users and media deliveries needed.'''
#     super(MarketingCampaignCase, self).setUp()

#     # Create users and partners associated
#     self.create_users()

#     # Create product
#     self.product = self.create_product()

#     # Create media types
#     self.media_type_cube = self.create_media_type(
#         'Media type cube test', self.product, 'cube')
#     self.media_type_container = self.create_media_type(
#         'Media type container test', self.product, 'container')

#     #####################################################################
#     # Object to test: self.user_input_01
#     # Media delivery: NO
#     # Answer lines: NO
#     #####################################################################
#     self.survey_01 = self.create_survey('Survey 01')
#     self.page_01 = self.create_page('Page 01', self.survey_01)
#     self.question_01 = self.create_question(
#         'Question 01', self.survey_01, self.page_01)
#     self.campaign_01 = self.create_campaign(
#         'Campaign 01', self.survey_01)
#     self.user_input_01 = self.create_user_input(
#         self.survey_01, self.campaign_01)

#     #####################################################################
#     # Object to test: self.user_input_02
#     # Media delivery: NO
#     # Answer lines: YES
#     # Media type associated with the question line: NO
#     #####################################################################
#     self.survey_02 = self.create_survey('Survey 02')
#     self.page_02 = self.create_page('Page 02', self.survey_02)
#     self.question_02 = self.create_question(
#         'Question 02', self.survey_02, self.page_02)
#     self.campaign_02 = self.create_campaign(
#         'Campaign 02', self.survey_02)
#     self.user_input_02 = self.create_user_input(
#         self.survey_02, self.campaign_02)

#     #####################################################################
#     # Object to test: self.user_input_03
#     # Media delivery: NO
#     # Answer lines: YES
#     # Media type associated with the question line: YES
#     # Category media type of question associated with the line is 'cube'
#     #   and the value is greater than 0: YES
#     #####################################################################
#     self.survey_03 = self.create_survey('Survey 03')
#     self.page_03 = self.create_page('Page 03', self.survey_03)
#     self.question_03 = self.create_question(
#         'Question 03', self.survey_03, self.page_03, self.media_type_cube)
#     self.campaign_03 = self.create_campaign(
#         'Campaign 03', self.survey_03)
#     self.user_input_03 = self.create_user_input(
#         self.survey_03, self.campaign_03)
#     self.create_user_input_line(
#         self.survey_03, self.question_03, self.user_input_03, 4)

#     #####################################################################
#     # Object to test: self.user_input_04
#     # Media delivery: NO
#     # Answer lines: YES
#     # Media type associated with the question line: YES
#     # Category media type of question associated with the line is 'cube'
#     #   and the value is greater than 0: NO
#     #####################################################################
#     self.survey_04 = self.create_survey('Survey 04')
#     self.page_04 = self.create_page('Page 04', self.survey_04)
#     self.question_04 = self.create_question(
#         'Question 04', self.survey_04, self.page_04,
#         self.media_type_container)
#     self.campaign_04 = self.create_campaign('Campaign 04', self.survey_04)
#     self.user_input_04 = self.create_user_input(
#         self.survey_04, self.campaign_04)
#     self.create_user_input_line(
#         self.survey_04, self.question_04, self.user_input_04, 4)

#     #####################################################################
#     # Object to test: self.user_input_05
#     # Media delivery: YES
#     # Answer lines: NO
#     #####################################################################
#     self.survey_05 = self.create_survey('Survey 05')
#     self.page_05 = self.create_page('Page 05', self.survey_05)
#     self.question_05 = self.create_question(
#         'Question 05', self.survey_05, self.page_05,
#         self.media_type_container)
#     self.campaign_05 = self.create_campaign('Campaign 05', self.survey_05)
#     self.media_delivery_05 = self.create_media_delivery(self.campaign_05)
#     self.user_input_05 = self.create_user_input(
#         self.survey_05, self.campaign_05, self.media_delivery_05)

#     #####################################################################
#     # Object to test: self.user_input_06
#     # Media delivery: YES
#     # Answer lines: YES
#     # Media type associated with the question line: NO
    ######################################################################
#     self.survey_06 = self.create_survey('Survey 06')
#     self.page_06 = self.create_page('Page 06', self.survey_06)
#     self.question_06 = self.create_question(
#         'Question 06', self.survey_06, self.page_06)
#     self.campaign_06 = self.create_campaign('Campaign 06', self.survey_06)
#     self.media_delivery_06 = self.create_media_delivery(self.campaign_06)
#     self.user_input_06 = self.create_user_input(
#         self.survey_06, self.campaign_06, self.media_delivery_06)
#     self.create_user_input_line(
#         self.survey_06, self.question_06, self.user_input_06, 4)

#     ######################################################################
#     # Object to test: self.user_input_07
#     # Media delivery: YES
#     # Answer lines: YES
#     # Media type associated with the question line: YES
######################################################################
#     self.survey_07 = self.create_survey('Survey 07')
#     self.page_07 = self.create_page('Page 07', self.survey_07)
#     self.question_07 = self.create_question(
#         'Question 07', self.survey_07, self.page_07,
#         self.media_type_container)
#     self.campaign_07 = self.create_campaign('Campaign 07', self.survey_07)
#     self.media_delivery_07 = self.create_media_delivery(self.campaign_07)
#     self.user_input_07 = self.create_user_input(
#         self.survey_07, self.campaign_07, self.media_delivery_07)
#     self.create_user_input_line(
#         self.survey_07, self.question_07, self.user_input_07, 4)

# # Test for change state in self.campaign_01
# def test_00_marketing_campaign(self):
#     '''Change the state of a campaign from 'draft' to 'running' and check
#     it.'''
#     self.campaign_01.state_running_set()
#     self.assertEqual(self.campaign_01.state, 'running')

# def test_01_marketing_campaign(self):
#     '''Change the state of a campaign from 'running' to 'done' and check
#     it. '''
#     # Habria que chequear previamente las colaboraciones pero no se puede,
#     # se crean desde la app
#     self.campaign_01.state_done_set()
#     self.assertEqual(self.campaign_01.state, 'done')

# # Test survey user input self.user_input_01
# def test_02_marketing_campaign(self):
#     '''Change the state of a survey user input to 'skip' and check it. '''
#     self.user_input_01.button_skip()
#     self.assertEqual(self.user_input_01.state, 'skip')

# def test_03_marketing_campaign(self):
#     '''Change the state of a survey user input to 'pending_review' and
#     check it. '''
#     self.user_input_01.button_pending_review()
#     self.assertEqual(self.user_input_01.state, 'pending_review')

# def test_04_marketing_campaign(self):
#     '''Change the state of a survey user input to 'done' and check it.
#     The answer has not a media delivery neither has got answer lines, so it
#     should not create media delivery.'''
#     self.user_input_01.button_done()
#     self.assertEqual(self.user_input_01.state, 'done')

#     now_str = str(datetime.now())
#     before_str = str((datetime.now() - dt.timedelta(minutes=1)))
#     media_deliveries = self.env['media.delivery'].search([
#         ('campaign_id', '=', self.campaign_01.id),
#         ('create_date', '<', now_str),
#         ('create_date', '>', before_str)])
#     self.assertEqual(len(media_deliveries), 0)

# def test_05_marketing_campaign(self):
#     '''Change the state of a survey user input to 'audited' and check it.
#     '''
#     self.user_input_01.button_audit()
#     self.assertEqual(self.user_input_01.state, 'audited')

# # Test survey user input self.user_input_02
# def test_06_marketing_campaign(self):
#     '''Change the state of a survey user input to 'skip' and check it. '''
#     self.user_input_02.button_skip()
#     self.assertEqual(self.user_input_02.state, 'skip')

# def test_07_marketing_campaign(self):
#     '''Change the state of a survey user input to 'pending_review' and
#     check it. '''
#     self.user_input_02.button_pending_review()
#     self.assertEqual(self.user_input_02.state, 'pending_review')

# def test_08_marketing_campaign(self):
#     '''Change the state of a survey user input to 'done' and check it.
#     The answer has not a media delivery associated and questions of its
#     lines have not media type, therefore, should not create any media
#     delivery.'''
#     self.user_input_02.button_done()
#     self.assertEqual(self.user_input_02.state, 'done')

#     now_str = str(datetime.now())
#     before_str = str((datetime.now() - dt.timedelta(minutes=1)))
#     media_deliveries = self.env['media.delivery'].search([
#         ('campaign_id', '=', self.campaign_02.id),
#         ('create_date', '<', now_str),
#         ('create_date', '>', before_str)])
#     self.assertEqual(len(media_deliveries), 0)

# def test_09_marketing_campaign(self):
#     '''Change the state of a survey user input to 'audited' and check it.
#     '''
#     self.user_input_02.button_audit()
#     self.assertEqual(self.user_input_02.state, 'audited')

# # Test survey user input self.user_input_03
# def test_10_marketing_campaign(self):
#     '''Change the state of a survey user input to 'skip' and check it. '''
#     self.user_input_03.button_skip()
#     self.assertEqual(self.user_input_03.state, 'skip')

# def test_11_marketing_campaign(self):
#     '''Change the state of a survey user input to 'pending_review' and
#     check it. '''
#     self.user_input_03.button_pending_review()
#     self.assertEqual(self.user_input_03.state, 'pending_review')

# def test_12_marketing_campaign(self):
#     '''Change the state of a survey user input to 'done' and check it.
#     The answer already has an associated media delivery, removes and
#     rebuilds. As the question has a media type cube associated, creates a
#     media for each of the units indicated.'''
#     self.user_input_03.button_done()
#     self.assertEqual(self.user_input_03.state, 'done')

#     now_str = str(datetime.now())
#     before_str = str((datetime.now() - dt.timedelta(minutes=1)))
#     media_deliveries = self.env['media.delivery'].search([
#         ('campaign_id', '=', self.campaign_03.id),
#         ('create_date', '<', now_str),
#         ('create_date', '>', before_str)])
#     self.assertEqual(len(media_deliveries), 1)
#     self.assertEqual(len(media_deliveries[0].media_lines), 1)

# def test_13_marketing_campaign(self):
#     '''Change the state of a survey user input to 'audited' and check it.
#     '''
#     self.user_input_03.button_audit()
#     self.assertEqual(self.user_input_03.state, 'audited')

# # Test survey user input self.user_input_04
# def test_14_marketing_campaign(self):
#     '''Change the state of a survey user input to 'skip' and check it. '''
#     self.user_input_04.button_skip()
#     self.assertEqual(self.user_input_04.state, 'skip')

# def test_15_marketing_campaign(self):
#     '''Change the state of a survey user input to 'pending_review' and
#     check it. '''
#     self.user_input_04.button_pending_review()
#     self.assertEqual(self.user_input_04.state, 'pending_review')

# def test_16_marketing_campaign(self):
#     '''Change the state of a survey user input to 'done' and check it.
#     The answer already has an associated media delivery, removes and
#     rebuilds. As the question has a media type container associated, not
#     creates any media.'''
#     self.user_input_04.button_done()
#     self.assertEqual(self.user_input_04.state, 'done')

#     now_str = str(datetime.now())
#     before_str = str((datetime.now() - dt.timedelta(minutes=1)))
#     media_deliveries = self.env['media.delivery'].search([
#         ('campaign_id', '=', self.campaign_04.id),
#         ('create_date', '<', now_str),
#         ('create_date', '>', before_str)])
#     self.assertEqual(len(media_deliveries), 1)
#     self.assertEqual(len(media_deliveries[0].media_lines), 4)

# def test_17_marketing_campaign(self):
#     '''Change the state of a survey user input to 'audited' and check it.
#     '''
#     self.user_input_04.button_audit()
#     self.assertEqual(self.user_input_04.state, 'audited')

# # Test survey user input self.user_input_05
# def test_18_marketing_campaign(self):
#     '''Change the state of a survey user input to 'skip' and check it. '''
#     self.user_input_05.button_skip()
#     self.assertEqual(self.user_input_05.state, 'skip')

# def test_19_marketing_campaign(self):
#     '''Change the state of a survey user input to 'pending_review' and
#     check it. '''
#     self.user_input_05.button_pending_review()
#     self.assertEqual(self.user_input_05.state, 'pending_review')

# def test_20_marketing_campaign(self):
#     '''Change the state of a survey user input to 'done' and check it.
#     The answer has not an associated media delivery neither any lines, so
#     not creates any media delivery line.'''
#     self.user_input_05.button_done()
#     self.assertEqual(self.user_input_05.state, 'done')

#     now_str = str(datetime.now())
#     before_str = str((datetime.now() - dt.timedelta(minutes=1)))
#     media_deliveries_lines = self.env['media.delivery.lines'].search([
#         ('delivery_id', '=', self.media_delivery_05.id),
#         ('create_date', '<', now_str),
#         ('create_date', '>', before_str)])
#     self.assertEqual(len(media_deliveries_lines), 0)

# def test_21_marketing_campaign(self):
#     '''Change the state of a survey user input to 'audited' and check it.
#     '''
#     self.user_input_05.button_audit()
#     self.assertEqual(self.user_input_05.state, 'audited')

# # Test survey user input self.user_input_06
# def test_22_marketing_campaign(self):
#     '''Change the state of a survey user input to 'skip' and check it. '''
#     self.user_input_06.button_skip()
#     self.assertEqual(self.user_input_06.state, 'skip')

# def test_23_marketing_campaign(self):
#     '''Change the state of a survey user input to 'pending_review' and
#     check it. '''
#     self.user_input_06.button_pending_review()
#     self.assertEqual(self.user_input_06.state, 'pending_review')

# def test_24_marketing_campaign(self):
#     '''Change the state of a survey user input to 'done' and check it.
#     The answer has not an associated media delivery neither any lines, so
#     not creates any media delivery line.'''
#     self.user_input_06.button_done()
#     self.assertEqual(self.user_input_06.state, 'done')

#     now_str = str(datetime.now())
#     before_str = str((datetime.now() - dt.timedelta(minutes=1)))
#     media_deliveries_lines = self.env['media.delivery.lines'].search([
#         ('delivery_id', '=', self.media_delivery_06.id),
#         ('create_date', '<', now_str),
#         ('create_date', '>', before_str)])
#     self.assertEqual(len(media_deliveries_lines), 0)

# def test_25_marketing_campaign(self):
#     '''Change the state of a survey user input to 'audited' and check it.
#     '''
#     self.user_input_06.button_audit()
#     self.assertEqual(self.user_input_06.state, 'audited')

# # Test survey user input self.user_input_07
# def test_26_marketing_campaign(self):
#     '''Change the state of a survey user input to 'skip' and check it. '''
#     self.user_input_07.button_skip()
#     self.assertEqual(self.user_input_07.state, 'skip')

# def test_27_marketing_campaign(self):
#     '''Change the state of a survey user input to 'pending_review' and
#     check it. '''
#     self.user_input_07.button_pending_review()
#     self.assertEqual(self.user_input_07.state, 'pending_review')

# def test_28_marketing_campaign(self):
#     '''Change the state of a survey user input to 'done' and check it.
#     The answer has not an associated media delivery but it has lines and
#     the question has a media type container associated, so it does not
#     create any media.'''
#     self.user_input_07.button_done()
#     self.assertEqual(self.user_input_07.state, 'done')

#     now_str = str(datetime.now())
#     before_str = str((datetime.now() - dt.timedelta(minutes=1)))
#     media_delivery_lines = self.env['media.delivery.lines'].search([
#         ('delivery_id', '=', self.media_delivery_07.id),
#         ('create_date', '<', now_str),
#         ('create_date', '>', before_str)])
#     self.assertEqual(len(media_delivery_lines), 4)

# def test_29_marketing_campaign(self):
#     '''Change the state of a survey user input to 'audited' and check it.
#     '''
#     self.user_input_07.button_audit()
#     self.assertEqual(self.user_input_07.state, 'audited')
