odoo.define('website_sale_rating_popoup.rating_popup', function(require) {
    'use strict'
    require('web.dom_ready')
    let Class = require('web.Class')
    let Ajax = require('web.ajax')
    let Core = require('web.core')
    let QWeb = Core.qweb
    let _t = Core._t
    let PortalChatter = require('portal.chatter').PortalChatter
    let LoadTemplate = Ajax.loadXML('/website_sale_rating_popoup/static/src/xml/website_sale_rating_popoup.xml', QWeb)
    let RatingPopup = Class.extend({
        title_selector: '#product_details h1',
        link_selector: '.js_wsrp_rating_popup_link',
        card_selector: '.js_wsrp_rating_popup_card',
        popup_template: 'website_sale_rating_popoup.rating_popup',
        hide_class: 'd-none',
        init: function () {
            self = this
            let $title = $(self.title_selector)
            if($title.length > 0){
                LoadTemplate.done(function(){
                    let $rating_popup = $(QWeb.render(self.popup_template))
                    $rating_popup.insertAfter($title)
                    let $rating_popup_link = $(self.link_selector)
                    $rating_popup_link.hover(function(){
                        $(self.card_selector).removeClass(self.hide_class)
                    })
                    $rating_popup.mouseleave(function(){}, function(){
                        $(self.card_selector).addClass(self.hide_class)
                    })
                })
            }
        },
    })
    PortalChatter.include({
        title_selector: '#product_details h1',
        header_selector: '#discussion .o_portal_chatter_header',
        link_selector: '.js_wsrp_rating_popup_link',
        static_selector: '.o_website_rating_static',
        counter_selector: '.o_message_counter',
        card_body_selector: '.js_wsrp_rating_popup_card .card-body',
        bars_selector: '.o_website_rating_progress_bars',
        reset_selector: '.o_website_rating_table_reset',
        rating_avg_selector: '.js_wsrp_rating_avg',
        rating_avg_value_selector: '.js_wsrp_rating_avg_value',
        rating_avg_heading_selector: '.o_website_rating_avg h1',
        start: function(){
            let self = this
            return this._super.apply(this, arguments).then(function(){
                let $chatter_header = $(self.header_selector)
                let $rating_popup_link = $(self.link_selector)
                let $rating_popup_card = $(self.card_body_selector)
                let $progress_bars = $chatter_header.find(self.bars_selector).clone()
                let $rating_avg = $(self.rating_avg_selector)
                let $rating_avg_value = $(self.rating_avg_value_selector)
                $chatter_header.find(self.static_selector).clone().appendTo($rating_popup_link)
                $chatter_header.find(self.counter_selector).clone().appendTo($rating_popup_link)
                $progress_bars.find(self.reset_selector).remove()
                $rating_avg_value.html($chatter_header.find(self.rating_avg_heading_selector).html())
                $chatter_header.find(self.static_selector).clone().insertBefore($rating_avg)
                $progress_bars.appendTo($rating_popup_card)
            })
        },
    })
    let rating_popup = new RatingPopup()
    return {
        rating_popup: rating_popup,
    }
})
