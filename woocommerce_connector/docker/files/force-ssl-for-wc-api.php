<?php
/**
 * Plugin Name: Force SSL for WooCommerce API
 * Description: Simula HTTPS para las peticiones de la API WooCommerce en entorno de desarrollo
 * Version: 1.0.0
 * Author: Trey
 */

add_filter('pre_option_woocommerce_force_ssl_checkout', '__return_false');

add_action('plugins_loaded', function() {
    // Solo simulamos HTTPS para la API legacy wc-api/v*.
    // NO forzamos HTTPS para /wp-json/wc/* porque la librería woocommerce-python
    // usa OAuth1 para conexiones HTTP. La firma OAuth1 se calcula sobre el esquema
    // http, y si el servidor ve https la firma no coincide -> 401.
    if (strpos($_SERVER['REQUEST_URI'], '/wc-api/') !== false) {
        $_SERVER['HTTPS'] = 'on';
    }
}, 1);
