odoo.define('portal_stock_picking_signature.pending_picking', function(require) {
    'use strict'
    require('web.dom_ready')
    let Class = require('web.Class')
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
        PendingPicking: PendingPicking,
        pending_picking: pending_picking,
    }
})
