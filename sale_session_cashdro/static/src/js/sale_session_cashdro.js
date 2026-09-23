odoo.define('sale_session_cashdro.sale_session_pay_cashdro', function (require) {
    'use strict'

    var core = require('web.core')
    var AbstractAction = require('web.AbstractAction')
    var framework = require('web.framework')
    var odoo_context = false
    var self = false

    var sale_session_cashdro = AbstractAction.extend({
        init: function(parent, action) {
            this._super.apply(this, arguments)
            this.actionManager = parent
            this.given_context = {}
            this.odoo_context = action.context
            this.controller_url = action.context.url
            this.currentURL = window.location.href
            if (action.context.context) {
                this.given_context = action.context.context
            }
            this.given_context.active_id = action.context.active_id || action.params.active_id
            this.given_context.model = action.context.active_model || false
            this.given_context.ttype = action.context.ttype || false
            this.given_context.template_name = action.params.template_name
            odoo_context = this.odoo_context
            self = this
            framework.blockUI()
            var msg = 'Conectando con Cashdro...'
            $.blockUI({
                'message': '<h2 class="text-white"><img src="/web/static/src/img/spin.png" class="fa-pulse"/>' +
                           '    <br />' + msg +
                           '</h2>'
            })
            console.log('ODOO CONTEXT')
            console.log(odoo_context)
            self._rpc({
                model: 'account.journal',
                method: 'start_operation',
                args: [odoo_context.sale_id],
                context: odoo_context,
            }).then(function (result){
                if (result.code == 1){
                    var max_attemps = 18
                    var interval = 10000
                    var attempt = 0
                    var timer = setInterval(function () {
                        attempt++
                        odoo_context.operation_id = result.data
                        if (attempt >= max_attemps) {
                            clearInterval(timer)
                            let msg_time_limit = 'Límite de tiempo superado para realizar el pago en Cashdro.'
                            $.blockUI({
                                'message': '<h2 class="text-white"><img src="/web/static/src/img/warning.png"/>' +
                                           '    <br />' + msg_time_limit +
                                           '</h2>'
                            })
                            self._rpc({
                                model: 'account.journal',
                                method: 'finish_operation',
                                args: [result.data],
                                context: odoo_context,
                            }).then(function (res){
                                setTimeout(function (){
                                    framework.redirect(self.currentURL)
                                }, 4000)
                            })
                        } else {
                            self._rpc({
                                model: 'account.journal',
                                method: 'ask_operation',
                                args: [result.data],
                                context: odoo_context,
                            }).then(function (res){
                                res.data = JSON.parse(res.data)
                                if (res.code == 1 && res.data.operation.state == 'F'){
                                    clearInterval(timer)
                                    self._rpc({
                                        model: 'account.invoice',
                                        method: 'print_invoice_report_and_payment_sale_session_cashdro',
                                        args: [odoo_context.sale_id],
                                        context: odoo_context,
                                    }).then(function (print){
                                        self.do_action(print)
                                        setTimeout(function () {
                                            framework.redirect(self.currentURL)
                                        }, 3000)
                                    })
                                } else if (res.code == 1 && res.data.operation.state == 'Q'){
                                    let url = '/session/' + odoo_context.sale_id + '/' + odoo_context.operation_id + '/' + odoo_context.journal_id + '/cancel'
                                    let msg_queue = 'Cashdro: La operación está en cola...'
                                    $.blockUI({
                                        'message': '<h2 class="text-white"><img src="/web/static/src/img/spin.png" class="fa-pulse"/>' +
                                                   '    <br />' + msg_queue +
                                                   '</h2>' +
                                                   '<br/>' + '<a href="' + url + '" role="button" style="text-decoration: none; background-color: #007BFF; color: #fff; padding: 10px 20px; border-radius: 5px; font-weight: bold;">Cancelar operación</a>'
                                        })
                                } else if (res.code == 1 && res.data.operation.state == 'E'){
                                    let url = '/session/' + odoo_context.sale_id + '/' + odoo_context.operation_id + '/' + odoo_context.journal_id + '/cancel'
                                    let msg_execute = 'Cashdro: La operación está en ejecución...'
                                    $.blockUI({
                                        'message': '<h2 class="text-white"><img src="/web/static/src/img/spin.png" class="fa-pulse"/>' +
                                                   '    <br />' + msg_execute +
                                                   '</h2>' +
                                                   '<br/>' + '<a href="' + url + '" role="button" style="text-decoration: none; background-color: #007BFF; color: #fff; padding: 10px 20px; border-radius: 5px; font-weight: bold;">Cancelar operación</a>'
                                    })
                                } else if (res.code == 1 && res.data.operation.state == 'I'){
                                    clearInterval(timer)
                                    let msg_not_found = 'Cashdro: La operación no existe'
                                    $.blockUI({
                                        'message': '<h2 class="text-white"><img src="/web/static/src/img/warning.png"/>' +
                                                   '    <br />' + msg_not_found +
                                                   '</h2>'
                                    })
                                    setTimeout(function (){
                                        framework.redirect(self.currentURL)
                                    }, 3000)
                                } else if (res.code == -1){
                                    clearInterval(timer)
                                    let msg_auth = 'Cashdro: ' + res.data
                                    $.blockUI({
                                        'message': '<h2 class="text-white"><img src="/web/static/src/img/warning.png"/>' +
                                                   '    <br />' + msg_auth +
                                                   '</h2>'
                                    })
                                    setTimeout(function (){
                                        framework.redirect(self.currentURL)
                                    }, 3000)
                                }
                            })
                        }
                    }, interval)
                } else {
                    let msg_error = 'Error al iniciar la operación con Cashdro: '
                    msg_error += result.data
                    $.blockUI({
                        'message': '<h2 class="text-white"><img src="/web/static/src/img/warning.png"/>' +
                                   '    <br />' + msg_error +
                                   '</h2>'
                    })
                    setTimeout(function () {
                        framework.redirect(self.currentURL)
                    }, 2000)
                }
            })
        }
    })
    core.action_registry.add(
        'sale_session_cashdro.sale_session_cashdro', sale_session_cashdro)
    return sale_session_cashdro
});
