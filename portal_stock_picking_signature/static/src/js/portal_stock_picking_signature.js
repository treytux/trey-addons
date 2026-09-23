odoo.define('portal_stock_picking_signature.pending_picking', function(require) {
    'use strict'
    require('web.dom_ready')
    let Class = require('web.Class')
    let Core = require('web.core')
    let QWeb = Core.qweb
    let Ajax = require('web.ajax')
    let PendingPicking = Class.extend({
        pending_picking_selector: '.js_psps_portal_signature',
        dom_ready: $.Deferred(),
        setup: false,
        ready: function(){
            let self = this
            return self.dom_ready.then(function() {}).promise()
        },
        init: function() {
            let self = this
            self.dom_ready.resolve()
            let $pending_picking = $(self.pending_picking_selector)
            let picking = $pending_picking.data('picking')
            if($pending_picking.length > 0){
                if (Number.isInteger(picking)){
                    let redirect_url = '/my/pending_picking/' + picking
                    window.location = redirect_url
                }
                setTimeout(function() {
                    window.location.reload()
                }, 1000 * 7)
            }
        },
    })
    let pending_picking = new PendingPicking()
    return {
        PendingPickings: PendingPickings,
        pending_picking: pending_picking,
    }
})
odoo.define('portal_stock_picking_signature.pending_pickings_list', function (require) {
    'use strict'

    require('web.dom_ready')
    let Class = require('web.Class')
    let Core = require('web.core')
    let QWeb = Core.qweb
    let Ajax = require('web.ajax')
    let PendingPickingsList = Class.extend({
        pending_pickings_table_selector: '.js_psps_pending_pickings_table',
        dom_ready: $.Deferred(),
        setup: false,
        ready: function(){
            let self = this
            return self.dom_ready.then(function() {}).promise()
        },
        init: function() {
            let self = this
            self.dom_ready.resolve()
            let $pending_pickings_table = $(self.pending_pickings_table_selector)
            if($pending_pickings_table.length > 0){
                setTimeout(function() {
                    window.location.reload()
                }, 1000 * 60)
            }
        },
    })
    let pending_pickings_list = new PendingPickingsList()
    return {
        PendingPickingsList: PendingPickingsList,
        pending_pickings_list: pending_pickings_list,
    }
})
odoo.define('portal_stock_picking_signature.pending_picking_detail', function (require) {
    'use strict'

    require('web.dom_ready')
    let Class = require('web.Class')
    let Core = require('web.core')
    let QWeb = Core.qweb
    let Ajax = require('web.ajax')
    let PendingPickingDetail = Class.extend({
        navspy_selector: '.li#navspy',
        dom_ready: $.Deferred(),
        setup: false,
        ready: function(){
            let self = this
            return self.dom_ready.then(function() {}).promise()
        },
        init: function() {
            let self = this
            self.dom_ready.resolve()
            $('body').scrollspy({ target: self.navspy_selector })
        },
    })
    let pending_picking_detail = new PendingPickingDetail()
    return {
        PendingPickingDetail: PendingPickingDetail,
        pending_picking_detail: pending_picking_detail,
    }
})
