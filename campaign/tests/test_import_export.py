# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp.tests.common import TransactionCase
import csv
import base64
from tempfile import NamedTemporaryFile


class ImportCampaignCase(TransactionCase):
    def create_users(self):
        # Admin
        self.partner_admin = self.env['res.partner'].create({
            'name': 'Admin',
            'company_id': self.ref('base.main_company'),
            'customer': False})
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_manager'),
            self.ref('campaign.group_campaign_admin')]
        self.user_admin = self.env['res.users'].create({
            'partner_id': self.partner_admin.id,
            'login': 'admin_test1@domain.es',
            'password': 'a',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]})

        # Campaign media manager
        self.partner_media_manager = self.env['res.partner'].create({
            'name': 'Media manager test 1',
            'company_id': self.ref('base.main_company'),
            'customer': False})
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_user'),
            self.ref('campaign.group_campaign_media_manager')]
        self.user_media_manager = self.env['res.users'].create({
            'partner_id': self.partner_media_manager.id,
            'login': 'media_manager_test1@domain.es',
            'password': '123',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]})

        # Campaign salesman manager
        self.partner_salesman_manager = self.env['res.partner'].create({
            'name': 'Salesman manager test 1',
            'company_id': self.ref('base.main_company'),
            'customer': False})
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_user'),
            self.ref('campaign.group_campaign_salesman_manager')]
        self.user_salesman_manager = self.env['res.users'].create({
            'partner_id': self.partner_salesman_manager.id,
            'login': 'salesman_manager_test1@domain.es',
            'password': '123',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]})

        # Campaign manager
        self.partner_manager = self.env['res.partner'].create({
            'name': 'Manager test 1',
            'company_id': self.ref('base.main_company'),
            'customer': False})
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_manager'),
            self.ref('campaign.group_campaign_manager')]
        self.user_manager = self.env['res.users'].create({
            'partner_id': self.partner_manager.id,
            'login': 'manager_test1@domain.es',
            'password': '123',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]})

        # Campaign survey auditor
        self.partner_survey_auditor = self.env['res.partner'].create({
            'name': 'Survey auditor test 1',
            'company_id': self.ref('base.main_company'),
            'customer': False})
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_user'),
            self.ref('campaign.group_campaign_survey_auditor')]
        self.user_survey_auditor = self.env['res.users'].create({
            'partner_id': self.partner_survey_auditor.id,
            'login': 'survey_auditor_test1@domain.es',
            'password': '123',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]})

        # Campaign media auditor
        self.partner_media_auditor = self.env['res.partner'].create({
            'name': 'Media auditor test 1',
            'company_id': self.ref('base.main_company'),
            'customer': False})
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_user'),
            self.ref('campaign.group_campaign_media_auditor')]
        self.user_media_auditor = self.env['res.users'].create({
            'partner_id': self.partner_media_auditor.id,
            'login': 'media_auditor_test1@domain.es',
            'password': '123',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]})

        # Campaign salesman
        self.partner_salesman = self.env['res.partner'].create({
            'name': 'Salesman test 1',
            'company_id': self.ref('base.main_company'),
            'customer': False})
        group_ids = [
            self.ref('base.group_user'),
            self.ref('base.group_partner_manager'),
            self.ref('base.group_sale_salesman'),
            self.ref('marketing.group_marketing_user'),
            self.ref('campaign.group_campaign_salesman')]
        self.user_salesman = self.env['res.users'].create({
            'partner_id': self.partner_salesman.id,
            'login': 'salesman_test1@domain.es',
            'password': '123',
            'company_id': self.ref('base.main_company'),
            'groups_id': [(6, 0, group_ids)]})

    def create_survey(self, name):
        return self.env['survey.survey'].create({'title': name})

    def create_supplier(self):
        self.supplier = self.env['res.partner'].create({
            'name': 'Supplier',
            'is_company': True,
            'supplier': True,
            'email': 'supplier@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'})

    def create_trade(self):
        self.trade = self.env['res.partner'].create({
            'name': 'Trade',
            'is_company': True,
            'trade': True,
            'email': 'trade@test.com',
            'street': 'C/Real, 33',
            'phone': '666335522'})

    def create_campaign(self, name, survey):
        return self.env['marketing.campaign'].create({
            'name': name,
            'supplier_salesman_user_id': self.user_salesman_manager.id,
            'supplier_delivery_user_id': self.user_media_manager.id,
            'user_id': self.user_manager.id,
            'survey_audit_id': self.user_survey_auditor.id,
            'media_audit_id': self.user_media_auditor.id,
            'business_survey_id': survey.id})

    def create_media_delivery(self, campaign):
        return self.env['media.delivery'].create({
            'supplier_delivery_id':
                campaign.supplier_delivery_user_id.partner_id.id,
            'campaign_id': campaign.id})

    def create_media(self):
        return self.env['media'].create({
            'name': 'Media test',
            'type_id': self.media_type_cube.id})

    def create_media_delivery_lines(self, media_delivery):
        return self.env['media.delivery.lines'].create({
            'delivery_id': media_delivery.id,
            'media_id': self.media.id,
            'requested': 3,
            'delivered': 0})

    def create_media_type(self, name, product, category):
        return self.env['media.type'].create({
            'name': name,
            'product_id': product.id,
            'category': category})

    def create_question(self, name, survey, page, media_type=None):
        data = {
            'question': name,
            'type': 'numerical_box',
            'survey_id': survey.id,
            'page_id': page.id}
        if media_type is not None:
            data.update({'media_type_id': media_type.id})
        return self.env['survey.question'].create(data)

    def create_user_input(self, survey, campaign, media_delivery=None):
        data = {
            'survey_id': survey.id,
            'campaign_id': campaign.id}
        if media_delivery is not None:
            data.update({'media_delivery_id': media_delivery.id})
        return self.env['survey.user_input'].create(data)

    def create_user_input_line(
            self, survey, question, user_input, value_number):
        return self.env['survey.user_input_line'].create({
            'answer_type': 'number',
            'survey_id': survey.id,
            'question_id': question.id,
            'user_input_id': user_input.id,
            'value_number': value_number})

    def create_product(self):
        return self.env['product.product'].create({'name': 'Product test'})

    def create_page(self, name, survey):
        return self.env['survey.page'].create({
            'title': name,
            'survey_id': survey.id})

    def setUp(self):
        '''Create marketing campaign, users and media deliveries needed.'''
        super(ImportCampaignCase, self).setUp()

        # Create users and partners associated
        self.create_users()

        # Create product
        self.product = self.create_product()

        # Create media types
        self.media_type_cube = self.create_media_type(
            'Media type cube test', self.product, 'cube')
        self.media_type_container = self.create_media_type(
            'Media type container test', self.product, 'container')

        # Create media
        self.media = self.create_media()

        self.survey = self.create_survey('Survey ')
        self.page = self.create_page('Page ', self.survey)
        self.question = self.create_question(
            'Question ', self.survey, self.page)
        self.campaign = self.create_campaign(
            'Campaign ', self.survey)
        self.user_input = self.create_user_input(
            self.survey, self.campaign)
        self.create_user_input_line(
            self.survey, self.question, self.user_input, 4)
        self.media_delivery_01 = self.create_media_delivery(self.campaign)
        self.media_delivery_01_line = self.create_media_delivery_lines(
            self.media_delivery_01)
        self.media_delivery_02 = self.create_media_delivery(self.campaign)
        self.media_delivery_02_line_01 = self.create_media_delivery_lines(
            self.media_delivery_02)
        self.media_delivery_02_line_02 = self.create_media_delivery_lines(
            self.media_delivery_02)

    def test_export_import_01(self):
        '''File with one row'''
        wiz_export = self.env['wiz.export.media.delivery'].with_context({
            'active_ids': [self.media_delivery_01.id],
            'active_model': 'media.delivery',
            'active_id': self.media_delivery_01.id}).create({})
        wiz_export.button_accept()
        self.assertTrue(wiz_export.ffile)
        data = base64.decodestring(wiz_export.ffile)
        self.assertIn('Line ID', data)

        file_obj = NamedTemporaryFile(
            'w+', suffix='.csv', delete=False)
        file_obj.write(base64.decodestring(wiz_export.ffile))
        path = file_obj.name
        file_obj.close()

        data = []
        with open(path, "rb") as fp:
            doc = csv.reader(
                fp, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
            data = [ln for ln in doc]
        self.assertIn('Line ID', data[0])
        self.assertIn('Campaign', data[0])
        self.assertIn('Trade ID', data[0])
        self.assertIn('Trade', data[0])
        self.assertIn('Trade address', data[0])
        self.assertIn('Trade phone', data[0])
        self.assertIn('Trade mobile', data[0])
        self.assertIn('Trade email', data[0])
        self.assertIn('Activity', data[0])
        self.assertIn('Name surveyed', data[0])
        self.assertIn('Function surveyed', data[0])
        self.assertIn('Opening days', data[0])
        self.assertIn('Comment', data[0])
        self.assertIn('Media type', data[0])
        self.assertIn('Requested', data[0])
        self.assertIn('Delivered', data[0])

        line_ids = [int(ln[0]) for ln in data if ln[0].isdigit()]

        def modify_file(column, value):
            with open(path, "wb") as fp:
                doc = csv.writer(
                    fp, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
                count = 0
                for ln in data:
                    count += 1
                    if count > 1:
                        ln[column] = value
                    doc.writerow(ln)

        modify_file(15, 9999)
        with open(path, "r") as fp:
            wiz_import = self.env['wiz.import.media.delivery'].create(
                {'ffile': base64.encodestring(fp.read())})
        wiz_import.button_simulation()
        wiz_import.button_done()
        for ln in self.env['media.delivery.lines'].browse(line_ids):
            self.assertEqual(ln.delivered, 9999)

        modify_file(15, 'ñáéíóúç')
        with open(path, "r") as fp:
            wiz_import = self.env['wiz.import.media.delivery'].create(
                {'ffile': base64.encodestring(fp.read())})
        self.assertRaises(Exception, wiz_import.button_simulation)
        self.assertRaises(Exception, wiz_import.button_done)

        modify_file(0, 'ñáéíóúç')
        with open(path, "r") as fp:
            wiz_import = self.env['wiz.import.media.delivery'].create(
                {'ffile': base64.encodestring(fp.read())})
        self.assertRaises(Exception, wiz_import.button_simulation)
        self.assertRaises(Exception, wiz_import.button_done)

        modify_file(0, -1)
        with open(path, "r") as fp:
            wiz_import = self.env['wiz.import.media.delivery'].create(
                {'ffile': base64.encodestring(fp.read())})
        self.assertRaises(Exception, wiz_import.button_simulation)
        self.assertRaises(Exception, wiz_import.button_done)

        modify_file(15, -9999)
        with open(path, "r") as fp:
            wiz_import = self.env['wiz.import.media.delivery'].create(
                {'ffile': base64.encodestring(fp.read())})
        self.assertRaises(Exception, wiz_import.button_simulation)
        self.assertRaises(Exception, wiz_import.button_done)

    def test_export_import_02(self):
        '''File with several rows'''
        wiz_export = self.env['wiz.export.media.delivery'].with_context({
            'active_ids': [self.media_delivery_02.id],
            'active_model': 'media.delivery',
            'active_id': self.media_delivery_02.id}).create({})
        wiz_export.button_accept()
        self.assertTrue(wiz_export.ffile)
        data = base64.decodestring(wiz_export.ffile)
        self.assertIn('Line ID', data)

        file_obj = NamedTemporaryFile(
            'w+', suffix='.csv', delete=False)
        file_obj.write(base64.decodestring(wiz_export.ffile))
        path = file_obj.name
        file_obj.close()

        data = []
        with open(path, "rb") as fp:
            doc = csv.reader(
                fp, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
            data = [ln for ln in doc]
        self.assertIn('Line ID', data[0])
        self.assertIn('Campaign', data[0])
        self.assertIn('Trade ID', data[0])
        self.assertIn('Trade', data[0])
        self.assertIn('Trade address', data[0])
        self.assertIn('Trade phone', data[0])
        self.assertIn('Trade mobile', data[0])
        self.assertIn('Trade email', data[0])
        self.assertIn('Activity', data[0])
        self.assertIn('Name surveyed', data[0])
        self.assertIn('Function surveyed', data[0])
        self.assertIn('Opening days', data[0])
        self.assertIn('Comment', data[0])
        self.assertIn('Media type', data[0])
        self.assertIn('Requested', data[0])
        self.assertIn('Delivered', data[0])

        line_ids = [int(ln[0]) for ln in data if ln[0].isdigit()]

        def modify_file(column, value):
            with open(path, "wb") as fp:
                doc = csv.writer(
                    fp, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
                count = 0
                for ln in data:
                    count += 1
                    if count > 1:
                        ln[column] = value
                    doc.writerow(ln)

        modify_file(15, 9999)
        with open(path, "r") as fp:
            wiz_import = self.env['wiz.import.media.delivery'].create(
                {'ffile': base64.encodestring(fp.read())})
        wiz_import.button_simulation()
        wiz_import.button_done()
        for ln in self.env['media.delivery.lines'].browse(line_ids):
            self.assertEqual(ln.delivered, 9999)

        modify_file(15, 'ñáéíóúç')
        with open(path, "r") as fp:
            wiz_import = self.env['wiz.import.media.delivery'].create(
                {'ffile': base64.encodestring(fp.read())})
        self.assertRaises(Exception, wiz_import.button_simulation)
        self.assertRaises(Exception, wiz_import.button_done)

        modify_file(0, 'ñáéíóúç')
        with open(path, "r") as fp:
            wiz_import = self.env['wiz.import.media.delivery'].create(
                {'ffile': base64.encodestring(fp.read())})
        self.assertRaises(Exception, wiz_import.button_simulation)
        self.assertRaises(Exception, wiz_import.button_done)

        modify_file(0, -1)
        with open(path, "r") as fp:
            wiz_import = self.env['wiz.import.media.delivery'].create(
                {'ffile': base64.encodestring(fp.read())})
        self.assertRaises(Exception, wiz_import.button_simulation)
        self.assertRaises(Exception, wiz_import.button_done)

        modify_file(15, -9999)
        with open(path, "r") as fp:
            wiz_import = self.env['wiz.import.media.delivery'].create(
                {'ffile': base64.encodestring(fp.read())})
        self.assertRaises(Exception, wiz_import.button_simulation)
        self.assertRaises(Exception, wiz_import.button_done)
