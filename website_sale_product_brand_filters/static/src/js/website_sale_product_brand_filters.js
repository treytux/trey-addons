odoo.define('website_sale_product_brand_filters.MoreList', function (require) {
    'use strict';
    require('web.dom_ready')
    let Class = require('web.Class')
    let MoreList = Class.extend({
        $list_search: $('.js_wspbf_search'),
        $more_btn: $('.js_wspbf_show_more_list_btn'),
        $show_more_list: false,
        $show_more_list_items: false,
        init: function () {
            let self = this
            self.$show_more_list = $('ul[data-show_more_list="' + self.$list_search.data('show_more_list') + '"]')
            self.$show_more_list_items = self.$show_more_list.find('li')
            if(self.$list_search.length > 0) {
                self.$list_search.on('keyup', function(){
                    let search_text = $(this).val().toLowerCase()
                    self.$show_more_list_items.each(function(index, element){
                        if($(this).text().toLowerCase().includes(search_text)){
                            $(this).show()
                        } else {
                            $(this).hide()
                        }
                    })
                    self.on_keyup_search()
                })
            }
            self.reset_list()
            if(self.$more_btn.length > 0) {
                self.$more_btn.on('click', function(e){
                    self.on_click_button(e)
                })
            }
        },
        reset_list: function () {
            let self = this
            self.$more_btn.show()
            if(self.$show_more_list.length > 0 && self.$show_more_list.hasClass('closed')) {
                self.$show_more_list_items.each(function(index, element){
                    if(index <= self.$show_more_list.data('show_more_list_items')){
                        $(this).show()
                    } else {
                        $(this).hide()
                    }
                })
            }
        },
        on_click_button: function (e) {
            let self = this
            e.preventDefault()
            if(self.$show_more_list.length > 0) {
                if(self.$show_more_list.hasClass('closed')){
                    self.$show_more_list.removeClass('closed')
                    self.$more_btn.find('.js_wspbf_label_more').addClass('d-none')
                    self.$more_btn.find('.js_wspbf_label_less').removeClass('d-none')
                } else {
                    self.$show_more_list.addClass('closed')
                    self.$more_btn.find('.js_wspbf_label_more').removeClass('d-none')
                    self.$more_btn.find('.js_wspbf_label_less').addClass('d-none')
                }
                self.$show_more_list_items.each(function(index, element){
                    if(index <= self.$show_more_list.data('show_more_list_items') || !self.$show_more_list.hasClass('closed')){
                        $(this).show()
                    } else {
                        $(this).hide()
                    }
                })
            }
        },
        on_keyup_search: function () {
            let self = this
            let search_text = self.$list_search.val()
            if(search_text.length > 0) {
                self.$more_btn.hide()
            } else {
                self.reset_list()
            }
        },
    })
    let show_more_list = new MoreList()
    return {
        MoreList: MoreList,
        show_more_list: show_more_list,
    }
})
