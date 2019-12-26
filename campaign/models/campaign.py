# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api
import logging
_log = logging.getLogger(__name__)


class MediaDelivery(models.Model):
    _name = 'media.delivery'
    _rec_name = 'campaign_id'

    name = fields.Char(
        string='Name',
        readonly=True)
    supplier_delivery_id = fields.Many2one(
        comodel_name='res.partner',
        string='Delivery supplier',
        required=True,
        domain=[('supplier', '=', 'True')])
    campaign_id = fields.Many2one(
        comodel_name='marketing.campaign',
        string='Campaign',
        required=True)
    date_delivery = fields.Date(
        string='Delivery date')
    media_lines = fields.One2many(
        comodel_name='media.delivery.lines',
        inverse_name='delivery_id',
        string='Media',
        domain=[('media_id.type_id.category', '=', 'cube')],
        copy=True)
    container_ids = fields.Many2many(
        comodel_name='container',
        relation='mediadelivery2container_rel',
        column1='mediadelivery_id',
        column2='container_id')
    cube_ids = fields.Many2many(
        comodel_name='cube',
        relation='mediadelivery2cube_rel',
        column1='mediadelivery_id',
        column2='cube_id')
    trade_id = fields.Many2one(
        comodel_name='res.partner',
        string='Trade',
        domain=[('trade', '=', True)])
    dealer_ids = fields.Many2many(
        comodel_name='res.users',
        relation='delivery2user_rel',
        column1='media_delivery_id',
        column2='dealer_id',
        domain=[('partner_id.dealer', '=', 'True')])
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('pending_delivery', 'Pending delivery'),
            ('pending_review', 'Pending review'),
            ('done', 'Done'),
            ('audited', 'Audited')],
        string='State',
        default='draft')

    @api.multi
    def action_pending_delivery(self):
        self.state = 'pending_delivery'

    @api.multi
    def action_pending_review(self):
        self.state = 'pending_review'

    @api.multi
    def action_done(self):
        self.state = 'done'

    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_audit(self):
        self.state = 'audited'

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            trade_name = record.trade_id and record.trade_id.name or ''
            name = trade_name + '/' + record.create_date
            res.append((record.id, name))
        return res


class CubeType(models.Model):
    _name = 'cube.type'

    name = fields.Char(
        string='Name',
        required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)


class Cube(models.Model):
    _name = 'cube'

    name = fields.Char(
        string='Name',
        required=True)
    type_id = fields.Many2one(
        comodel_name='cube.type',
        string='Cube type',
        required=True)


class ContainerType(models.Model):
    _name = 'container.type'

    name = fields.Char(
        string='Name',
        required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)


class Container(models.Model):
    _name = 'container'

    name = fields.Char(
        string='Name',
        required=True)
    type_id = fields.Many2one(
        comodel_name='container.type',
        string='Container type',
        required=True)
    container_location_id = fields.Many2one(
        comodel_name='container.location',
        string='Location')


class ContainerLocation(models.Model):
    _name = 'container.location'

    name = fields.Char(
        string='Name')
    container_id = fields.Many2one(
        comodel_name='container',
        string='Container',
        required=True)
    address = fields.Char(
        string='Address')
    coordinates = fields.Char(
        string='Coordinates',
        help='Latitude and Longitude comma separated')


class MediaType(models.Model):
    _name = 'media.type'

    name = fields.Char(
        string='Name',
        required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)
    category = fields.Selection(
        selection=[
            ('cube', 'Cube'),
            ('container', 'Container')],
        string='Category')
    geolocation = fields.Char(
        string='Geolocation')


class MediaDeliveryLines(models.Model):
    _name = 'media.delivery.lines'

    delivery_id = fields.Many2one(
        comodel_name='media.delivery',
        string='Media delivery',
        required=True,
        ondelete='cascade')
    media_id = fields.Many2one(
        comodel_name='media',
        string='Media',
        required=True)
    media_type = fields.Char(
        related='media_id.type_id.name')
    requested = fields.Integer(
        string='Requested',
        default=1)
    delivered = fields.Integer(
        string='Delivered',
        default=0)


class Media(models.Model):
    _name = 'media'

    name = fields.Char(
        string='Name',
        required=True)
    type_id = fields.Many2one(
        comodel_name='media.type',
        string='Media type',
        required=True)
    address = fields.Char(
        string='Address')
    coordinates = fields.Char(
        string='Coordinates',
        help='Latitude and longitude comma separated. For example: '
             '40.4081667,-3.6913427')


class Collaboration(models.Model):
    _name = 'collaboration'
    _rec_name = 'campaign_id'
    _order = 'trade_id'

    name = fields.Char(
        string='Name')
    campaign_id = fields.Many2one(
        comodel_name='marketing.campaign',
        string='Campaign',
        required=True)
    trade_id = fields.Many2one(
        comodel_name='res.partner',
        string='Trade',
        required=True,
        domain=[('trade', '=', True)])
    collaborate = fields.Selection(
        selection=[
            ('yes', 'Yes'),
            ('no', 'No')],
        string='Collaborate',
        default='yes')
    reason_id = fields.Many2one(
        comodel_name='collaboration.reason',
        string='Reason')
    # reason = fields.Text(
    #     string='Reason')
    survey_input_id = fields.Many2one(
        comodel_name='survey.user_input',
        string='Answer survey')
    media_delivery_id = fields.Many2one(
        comodel_name='media.delivery',
        string='Media delivery')
    zip_id = fields.Many2one(
        comodel_name='res.better.zip',
        compute='_compute_zip',
        store=True,
        string='Zip')

    @api.one
    @api.depends('trade_id')
    def _compute_zip(self):
        self.zip_id = (
            self.trade_id.zip_id and self.trade_id.zip_id.id or None)
