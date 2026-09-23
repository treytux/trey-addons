odoo.define('portal_stock_picking_signature.delivery_proof', function (require) {
    'use strict'
    require('web.dom_ready')
    const ajax = require('web.ajax')
    const core = require('web.core')
    const _t = core._t

    const $form = $('.js_psps_proof_form')
    if (!$form.length) {
        return $.Deferred().reject().promise()
    }
    const pickingId = $form.data('pickingId')
    const token = $form.data('token')
    const $input = $form.find('.js_psps_proof_input')
    const $preview = $form.find('.js_psps_proof_preview')
    const $name = $form.find('.js_psps_proof_name')
    const $submit = $form.find('.js_psps_proof_submit')
    const $error = $form.find('.o_psps_proof_error')
    let dataUrl = false

    const showError = function (message) {
        $error.text(message).prop('hidden', false)
    }

    $input.on('change', function () {
        const file = this.files && this.files[0]
        dataUrl = false
        $submit.prop('disabled', true)
        $error.prop('hidden', true).text('')
        $preview.prop('hidden', true).attr('src', '')
        if (!file) {
            return
        }
        const reader = new FileReader()
        reader.onload = function (ev) {
            dataUrl = ev.target.result
            $preview.attr('src', dataUrl).prop('hidden', false)
            $submit.prop('disabled', false)
        }
        reader.onerror = function () {
            showError(_t('The photo could not be read.'))
        }
        reader.readAsDataURL(file)
    })

    $submit.on('click', function () {
        if (!dataUrl) {
            return
        }
        $submit.prop('disabled', true)
        $error.prop('hidden', true).text('')
        const file = $input[0].files[0] || {}
        ajax.jsonRpc(
            '/my/pending_picking/' + pickingId + '/accept_photo', 'call', {
                access_token: token,
                name: $name.val(),
                filename: file.name,
                image: dataUrl,
            }
        ).then(function (data) {
            if (data && data.error) {
                showError(data.error)
                $submit.prop('disabled', false)
                return
            }
            if (data && data.redirect_url) {
                window.location = data.redirect_url
            } else {
                window.location.reload()
            }
        }).guardedCatch(function () {
            showError(_t('The photo could not be uploaded.'))
            $submit.prop('disabled', false)
        })
    })
})
