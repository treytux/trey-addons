# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp.tests import common

EMAIL_TPL = """Return-Path: <whatever-2a840@postmaster.twitter.com>
X-Original-To: {email_to}
Delivered-To: {email_to}
To: {email_to}
Received: by mail1.openerp.com (Postfix, from userid 10002)
    id 5DF9ABFB2A; Fri, 10 Aug 2012 16:16:39 +0200 (CEST)
Message-ID: {msg_id}
Date: Tue, 29 Nov 2011 12:43:21 +0530
From: {email_from}
MIME-Version: 1.0
Subject: {subject}
Content-Type: text/plain; charset=ISO-8859-1; format=flowed

Hello,

This email should create a new entry in your sale. Please check that it
effectively works.

Thanks,

--
Raoul Boitempoils
Integrator at Agrolait"""


class TestSaleDisableAutosubscription(common.TransactionCase):

    def setUp(self):
        super(TestSaleDisableAutosubscription, self).setUp()
        self.server = self.env['fetchmail.server'].create({
            'name': 'Demo server',
            'type': 'pop',
            'server': 'pop3.example.com',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'email': 'partnertest@test.com',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })

    def test_sale_no_autoadd_partner_as_follower_on_confirm(self):
        self.assertFalse(
            self.sale.partner_id in self.sale.message_follower_ids)
        self.sale.action_button_confirm()
        self.assertFalse(
            self.sale.partner_id in self.sale.message_follower_ids)

    def test_thread_not_add_partner_to_followers(self):
        self.assertFalse(
            self.sale.partner_id in self.sale.message_follower_ids)
        comments = len(self.sale.message_ids)
        msg = 'This is a test'
        self.sale.with_context(
            fetchmail_server_id=self.server.id).message_process(
                self.sale._name, msg, thread_id=self.sale.id)
        self.sale.refresh()
        self.assertNotEqual(comments, len(self.sale.message_ids))
        self.assertEqual(comments + 1, len(self.sale.message_ids))
        self.assertFalse(
            self.sale.partner_id in self.sale.message_follower_ids)

    def test_thread_force_add_partner_to_followers(self):
        self.assertFalse(
            self.sale.partner_id in self.sale.message_follower_ids)
        comments = len(self.sale.message_ids)
        self.env['mail.thread'].with_context(
            fetchmail_server_id=self.server.id).message_process(
                self.sale._name,
                EMAIL_TPL.format(
                    email_from='spambot@example.com',
                    email_to='partnertest@test.com',
                    subject='Im a robot, hello',
                    msg_id='<filter.happier.more.productive@example.com>'
                ).encode('utf-8'),
                thread_id=self.sale.id)
        self.sale.refresh()
        self.assertNotEqual(comments, len(self.sale.message_ids))
        self.assertEqual(comments + 1, len(self.sale.message_ids))
        self.assertFalse(
            self.sale.partner_id in self.sale.message_follower_ids)

    def test_message_post_not_add_partner_to_followers(self):
        self.assertFalse(
            self.sale.partner_id in self.sale.message_follower_ids)
        comments = len(self.sale.message_ids)
        msg = 'This is a test'
        self.sale.message_post(body=msg)
        self.assertNotEqual(comments, len(self.sale.message_ids))
        self.assertEqual(comments + 1, len(self.sale.message_ids))
        self.assertFalse(
            self.sale.partner_id in self.sale.message_follower_ids)
