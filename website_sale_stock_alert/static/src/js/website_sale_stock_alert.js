(function() {
    'use strict'
    let website = openerp.website
    website.ready().done(function() {
        let $alert_btn = $('a.o_wssa_stock_alert')
        if($alert_btn.length) {
            let product_id = $alert_btn.data('product-product-id')
            $alert_btn.on('click', function(e){
                if($alert_btn.attr('disabled')){
                    e.preventDefault()
                } else {
                    $alert_btn.attr('disabled', 'disabled')
                    openerp.jsonRpc('/shop/stock_alert', 'call', {
                        'product_id': Number(product_id)
                    }).then(function(data){
                        if(data === 'true'){
                            $alert_btn.attr('disabled', 'disabled')
                            $('#js_wssa_stock_alert_modal_success').modal('show')
                        } else {
                            $alert_btn.removeAttr('disabled')
                            $('#js_wssa_stock_alert_modal_error').modal('show')
                        }
                    })
                }
            })
        }
    })
}())
