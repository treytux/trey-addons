odoo.define('website_sale_delivery_integra2.tracking_info', function (require) {
    'use strict'

    require('web.dom_ready')
    let Ajax = require('web.ajax')
    let Class = require('web.Class')
    let TrackingInfo = Class.extend({
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise()
        },
        init: function () {
            this.dom_ready.resolve()
            this.get_tracking_info()
        },
        get_tracking_info: function(){
            let $tracking_info  = $('.js_wsdi_tracking_info')
            let $tracking_info_list  = $tracking_info.find('ul')
            let $get_tracking_info_integra2  = $('.js_wsdi_get_tracking_info_integra2')
            if($tracking_info.length > 0 && $tracking_info_list.length > 0 && $get_tracking_info_integra2.length > 0){
                $get_tracking_info_integra2.on('click', function(e){
                    $tracking_info.addClass('d-none')
                    let get_tracking_info_integra2_url  = $(this).attr('href')
                    e.preventDefault()
                    Ajax.jsonRpc('/get_tracking_info_integra2', 'call', {
                        'url': get_tracking_info_integra2_url
                    }).then(function (data) {
                        $tracking_info.removeClass('d-none')
                        $tracking_info_list.empty()
                        $.each(JSON.parse(data), function (key, value) {
                            $('<li class="list-unstyled-item">' + key + ': ' + value + '</li>').appendTo($tracking_info_list)
                        })
                    })
                })
            }
        },
    })
    let tracking_info = new TrackingInfo()
    return {
        TrackingInfo: TrackingInfo,
        tracking_info: tracking_info,
    }
})
