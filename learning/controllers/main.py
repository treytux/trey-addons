# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
import openerp.addons.website_sale.controllers.main as main
from openerp.addons.website.models.website import slug
from openerp import http
from openerp.http import request
from openerp import fields
import logging


_log = logging.getLogger(__name__)


class LearningTraining(http.Controller):
    def _get_partner(self):
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

    def _get_partner_subscriptions(self, partner_id):
        env = request.env

        return env['learning.subscription'].search(
            [('partner_id', '=', partner_id),
             ('date_end', '>=', fields.Date.today())])

    def _active_subscription(self, partner_id, training_ids):
        active_subscription = True

        subscriptions = self._get_partner_subscriptions(partner_id)

        if subscriptions:
            for training_id in training_ids:
                if training_id not in subscriptions.ids:
                    active_subscription = False

        return active_subscription

    @http.route([
        '/course/<model("learning.training"):training>',
        '/curso/<model("learning.training"):training>'],
        type='http',
        auth='user',
        website=True
    )
    def training(self, training=None, **kwargs):
        """
        Muestra el contenido de un curso
        """
        training = len(training) > 0 and training[0] or training
        partner = self._get_partner()
        subscriptions = None
        if training and partner:
            subscriptions = self._get_partner_subscriptions(partner.id)
            if subscriptions:
                for subscription in subscriptions:
                    if subscription.training_id.id == training.id:
                        if subscription.remaining_days > 0:
                            return request.website.render(
                                'learning.training',
                                {'training': len(training) > 0 and
                                 training[0] or training})
                        else:
                            return request.redirect("/shop/product/%s" %
                                                    slug(training.template_id))
        return request.redirect('/')


class LearningTrainingLesson(http.Controller):

    def _get_partner(self):
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

    def _get_partner_subscriptions(self, partner_id):
        env = request.env

        return env['learning.subscription'].search(
            [('partner_id', '=', partner_id),
             ('date_end', '>=', fields.Datetime.now())])

    def _active_subscription(self, partner_id, training_ids):
        active_subscription = True

        subscriptions = self._get_partner_subscriptions(partner_id)

        if subscriptions:
            for training_id in training_ids:
                if training_id not in subscriptions.ids:
                    active_subscription = False

        return active_subscription

    @http.route([
        '/lesson/<model("learning.training.lesson"):lesson>',
        '/leccion/<model("learning.training.lesson"):lesson>'],
        type='http',
        auth='user',
        website=True
    )
    def lesson(self, lesson=None, **kwargs):
        """
        Muestra el contenido de una lección
        """
        lesson = len(lesson) > 0 and lesson[0] or lesson
        partner = self._get_partner()
        subscriptions = None
        if lesson and partner:
            subscriptions = self._get_partner_subscriptions(partner.id)
            if subscriptions:
                for subscription in subscriptions:
                    if lesson.id in \
                       subscription.training_id.lesson_line.ids:
                        if subscription.remaining_days > 0:
                            return request.website.render(
                                'learning.lesson',
                                {'lesson': lesson})
                        else:
                            return request.redirect('/shop/product/%s' % (
                                slug(lesson.training_id.template_id)))
        return request.redirect('/')


class WebsiteSale(main.website_sale):
    @http.route(['/shop/product/<model("product.template"):product>'],
                type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        r = super(WebsiteSale, self).product(product, category, search,
                                             **kwargs)
        partner = self._get_partner()
        r.qcontext['subscription'] = False
        if partner and r.qcontext['product'].training_ids:
            r.qcontext['subscription'] = self._active_subscription(
                partner, r.qcontext['product'].training_ids.ids)

        return r

    def _get_partner_subscriptions(self, partner_id):
        env = request.env
        subscriptions = env['learning.subscription'].search([
            ('partner_id', '=', partner_id),
            ('date_end', '>=', fields.Datetime.now())])

        return subscriptions

    def _active_subscription(self, partner_id, training_ids):
        active_subscription = False
        subscriptions = self._get_partner_subscriptions(partner_id.id)
        if subscriptions:
            for subscription in subscriptions:
                if subscription.training_id.id in training_ids:
                    active_subscription = True

        return active_subscription

    def _get_partner(self):
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

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>'
        '/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', **post):
        r = super(WebsiteSale, self).shop(page=page, category=category,
                                          search=search, **post)
        partner_id = self._get_partner()
        values = []
        if partner_id:
            subscriptions = self._get_partner_subscriptions(partner_id.id)
            if subscriptions:
                for product in r.qcontext['products']:
                    for subscription in subscriptions:
                        if subscription.training_id.template_id.id == \
                                product.id:
                            values.append(product.id)
        r.qcontext['subscriptions'] = values
        return r

    ##########################################################################
    # Por si se quiere crear la suscripcion en estado borrador al confirmar el
    # pedido
    ##########################################################################
    # @http.route(['/shop/confirmation'], type='http',
    #             auth="public", website=True)
    # def payment_confirmation(self, **post):
    #     res = super(WebsiteSale, self).payment_confirmation(**post)
    #     training_obj = request.env['learning.training']
    #     subscription_obj = request.env['learning.subscription']
    #     for order in res.qcontext.get('order'):
    #         for line in order.order_line:
    #             if line.product_id.product_tmpl_id.subscription_ok:
    #                 training = training_obj.search([
    #                     ('template_id', '=',
    #                         line.product_id.product_tmpl_id.id)])
    #                 values = {
    #                     'state': 'draft',
    #                     'name': order.partner_id.name + "/" +
    #                     line.product_id.name_template,
    #                     'exam_attempts': training.exam_id.exam_attempts,
    #                     'partner_id': order.partner_id.id,
    #                     'order_id': order and order[0].id or False,
    #                     'training_id': training.id,
    #                     # 'lesson_line': lesson_line or False,
    #                     # 'exam_line': exam_line or False
    #                 }
    #                 subscription_obj.create(values)
    #     return res
