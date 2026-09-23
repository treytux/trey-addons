odoo.define('portal_stock_picking_signature.sign_terminal_sale_session', function (require) {
    'use strict'

    var core = require('web.core')
    var AbstractAction = require('web.AbstractAction')
    var framework = require('web.framework')
    var odoo_context = false
    var self = false

    var picking_signature_sale_session = AbstractAction.extend({
        init: function(parent, action) {
            this._super.apply(this, arguments)
            this.actionManager = parent
            this.given_context = {}
            this.odoo_context = action.context
            this.controller_url = action.context.url
            this.currentURL = window.location.href
            framework.blockUI()
            var msg = 'Firme el albarán'
            var $blockMessage = $(
                '<div>' +
                '    <h2 class="text-white"><img src="/web/static/src/img/spin.png" class="fa-pulse"/>' +
                '        <br />' + msg +
                '    </h2>' +
                '    <button type="button" class="btn btn-secondary mt-3 o_psps_cancel_signature_btn">Cancelar firma</button>' +
                '</div>'
            )
            $.blockUI({'message': $blockMessage})
            if (action.context.context) {
                this.given_context = action.context.context
            }
            this.given_context.active_id = action.context.active_id || action.params.active_id
            this.given_context.model = action.context.active_model || false
            this.given_context.ttype = action.context.ttype || false
            this.given_context.template_name = action.params.template_name
            odoo_context = this.odoo_context
            self = this
            var max_attemps = 15
            var interval = 5000
            var attempt = 0
            var cancelSignature = function (message) {
                clearInterval(timer)
                $.blockUI({
                    'message': '<h2 class="text-white"><img src="/web/static/src/img/warning.png"/>' +
                               '    <br />' + message +
                               '</h2>'
                })
                self._rpc({
                    model: 'stock.picking',
                    method: 'set_cancel_pending_picking',
                    args: [odoo_context.picking_id],
                    context: odoo_context,
                }).then(function (outcome) {
                    setTimeout(function () {
                        framework.redirect(self.currentURL)
                    }, 2000)
                })
            }
            $blockMessage.on('click', '.o_psps_cancel_signature_btn', function () {
                cancelSignature('Se ha cancelado la firma del albarán.')
            })
            var timer = setInterval(function () {
                attempt++
                if (attempt >= max_attemps) {
                    cancelSignature('Límite de tiempo para firmar superado.')
                } else {
                    self._rpc({
                        model: 'stock.picking',
                        method: 'get_pending_picking_sign_portal',
                        args: [odoo_context.picking_id],
                        context: odoo_context,
                    }).then(function (result) {
                        if (result == 'signed'){
                            clearInterval(timer)
                            self._rpc({
                                model: 'stock.picking',
                                method: 'print_picking_report_sale_session',
                                args: [odoo_context.picking_id],
                                context: odoo_context,
                            }).then(function (res) {
                                self.do_action(res)
                                setTimeout(function() {
                                    framework.redirect(self.currentURL)
                                }, 4000)
                            })
                        } else if (result == 'cancel') {
                            let cancel_msg = 'Se ha cancelado la firma del albarán.'
                            $.blockUI({
                                'message': '<h2 class="text-white"><img src="/web/static/src/img/warning.png"/>' +
                                           '    <br />' + cancel_msg +
                                           '</h2>'
                            })
                            setTimeout(function () {
                                framework.redirect(self.currentURL)
                            }, 2000)
                        }
                    })
                }
            }, interval)
        }
    })
    core.action_registry.add(
        'portal_stock_picking_signature.picking_signature_sale_session',
        picking_signature_sale_session)
    return picking_signature_sale_session
})
