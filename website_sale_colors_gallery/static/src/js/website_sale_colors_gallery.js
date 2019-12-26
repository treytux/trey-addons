odoo.define('website_sale_colors_gallery.ColorsGallery', function (require) {
    'use strict';
    require('web.dom_ready')

    let Class = require('web.Class')
    let ajax = require('web.ajax');
    let core = require('web.core');
    let qweb = core.qweb;
    ajax.loadXML('/website_sale_colors_gallery/static/src/xml/website_sale_colors_gallery.xml', qweb);

    let ColorsGallery = Class.extend({
        colors_selector: '.o_wscg_colors[data-type="carousel"]',
        carousel_selector: '.carousel',
        cols: 12,
        items_per_slide: 2,
        item_cols: 6,
        interval: 1500,
        init: function () {
            let self = this
            let $products = $('.oe_product')
            if($products.length > 0) {
                $products.each(function(){
                    $(this).hover(
                        function() {
                            let $colors = $(this).find(self.colors_selector)
                            if($colors.length > 0) {
                                let $carousel_images = $colors.find('img')
                                if($carousel_images.length > 1) {
                                    if($colors[0].hasAttribute('data-items_per_slide')){
                                        self.items_per_slide = $colors.data('items_per_slide')
                                        self.item_cols = parseInt(self.cols / self.items_per_slide)
                                    }
                                    if($colors[0].hasAttribute('data-interval')){
                                        self.interval = $colors.data('interval')
                                    }
                                    $colors.append(qweb.render('colors_gallery.carousel', {'interval': self.interval}))
                                    let $carousel = $colors.find(self.carousel_selector)
                                    let $carousel_inner = $carousel.find('.carousel-inner')
                                    $carousel_images.each(function(){
                                        $carousel_inner.append($(this).clone())
                                    })
                                    let $carousel_inner_images = $carousel_inner.find('img')
                                    $carousel_inner_images.each(function(){
                                        $(this).wrap(qweb.render('colors_gallery.carousel_item_img_wrap', {'item_cols': self.item_cols}))
                                    })
                                    let $carousel_inner_cols = $carousel_inner.find('.col-' + self.item_cols)
                                    for(var i = 0; i < $carousel_inner_cols.length; i+=self.items_per_slide) {
                                        $carousel_inner_cols.slice(i, i+self.items_per_slide).wrapAll(qweb.render('colors_gallery.carousel_item', {}));
                                    }
                                    $carousel_inner.find('.carousel-item').first().addClass('active')
                                    $carousel.carousel()
                                }
                            }
                        }, function() {
                            let $colors = $(this).find(self.colors_selector)
                            if($colors.length > 0) {
                                let $carousel = $colors.find(self.carousel_selector)
                                if($carousel.length > 0) {
                                    $carousel.remove()
                                }
                            }
                        }
                    )
                })
            }
        },
    })
    let colors_gallery = new ColorsGallery()
    return {
        ColorsGallery: ColorsGallery,
        colors_gallery: colors_gallery,
    }
})
