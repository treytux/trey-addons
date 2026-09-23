<?php
/**
 * Class with endpoint for products.
 *
 * @package WooDoo
 */

// If this file is called directly, abort.
if ( ! defined( 'WPINC' ) ) {
	die;
}

/**
 * API CUSTOM ENDPOINTS FOR PRODUCTS
 */
class CL_SendtoOdoo {

	/**
	 * Endpoint url.
	 *
	 * @var string
	 */
	private $url = 'http://futurnet.treytux.com:8069';

	/**
	 * Session ID.
	 *
	 * @var string
	 */
	private $session_id = '';

	/**
	 * BD name
	 *
	 * @var string
	 */
	private $db = 'futurnet_migrated';

	/**
	 * Username of odoo user.
	 *
	 * @var string
	 */
	private $user = 'futurnet_json';

	/**
	 * User Password.
	 *
	 * @var string
	 */
	private $password = 'QqS13';

	/**
	 * Function construct.
	 */
	public function __construct() {

	}

	/**
	 * Undocumented function
	 *
	 * @param String $endpoint Endpoint.
	 * @param Array  $params Params.
	 * @return $result
	 */
	public function request( $endpoint, $params ) {
		$ch = curl_init( $this->url . $endpoint );
		curl_setopt( $ch, CURLOPT_POST, 1);
		curl_setopt( $ch, CURLOPT_POSTFIELDS, json_encode( $params ) );
		curl_setopt(
			$ch,
			CURLOPT_HTTPHEADER,
			array(
				'Content-Type: application/json',
				'Accept: application/json',
				'X-Openerp-Session-Id:' . $this->session_id,
			)
		);
		curl_setopt( $ch, CURLOPT_VERBOSE, true );
		curl_setopt( $ch, CURLOPT_RETURNTRANSFER, true );
		curl_setopt( $ch, CURLOPT_HEADER, 1 );
		$response = curl_exec( $ch );
		curl_close( $ch );

		$lines   = explode( "\n", $response );
		$headers = array();
		$body    = "";
		foreach ( $lines as $num => $line){
			$l = str_replace( "\r", "", $line );
			if ( trim( $l ) == "" ) {
				$headers = array_slice( $lines, 0, $num );
				$body = $lines[$num + 1];
				break;
			}
		}
		preg_match_all( '/^Set-Cookie:\s*([^;]*)/mi', $response, $matches );        // get cookie
		$cookies = array();
		foreach ( $matches[1] as $item ) {
			parse_str( $item, $cookie );
			$cookies = array_merge( $cookies, $cookie );
		}
		if ( array_key_exists( 'session_id', $cookies ) ) {
			$this->session_id = $cookies['session_id'];
		}
		$result = json_decode( $body, true );
		if ( array_key_exists( 'error', $result ) ) {
			$error = $result['error'];
			echo '(' . $error['code'] . ') ' . $error['message'] . '\n';
			echo $error['data']['debug'] . '\n';
			return $result;
		}
		return $result;
	}

	/**
	 * Login on Odoo
	 *
	 * @return Boolean
	 */
	private function login() {
		$response = $this->request(
			'/web/session/authenticate',
			array(
				'params' => array(
					'db' => $this->db,
					'login' => $this->user,
					'password' => $this->password,
				),
			)
		);
		if ( array_key_exists( 'result', $response ) && array_key_exists( 'uid', $response['result'] ) ) {
				return true;
		}
		return false;
	}

	/**
	 * Send order to odoo
	 *
	 * @param int $order_id the order id.
	 * @return void
	 */
	public function send_order( $order_id ) {
		$order           = wc_get_order( $order_id );
		$order_data      = $order->get_data();

		$json_order_data = wp_json_encode( $order_data );
		if ( ! $this->login() ) {
			print( 'Login error.' );
			exit( -1 );
		}
		$pedido_formatted = array(
			'name'                => $order_id,
			'partner'             => array(
				'name'   => $order->get_billing_first_name() . ' ' . $order->get_billing_last_name(),
				'street' => $order->get_billing_address_1() . ' ' . $order->get_billing_address_2(),
				'email'  => $order->get_billing_email(),
			),
			'partner_shipping'    => array(
				'name'   => $order->get_shipping_first_name() . ' ' . $order->get_shipping_last_name(),
				'street' => $order->get_shipping_address_1() . ' ' . $order->get_shipping_address_2(),
				'email'  => get_post_meta( $order->get_id(), '_shipping_email', true ),
			),
			'order_line'          => array(),
			'note'                => $order->get_customer_note(),
			'state'               => 'confirmed',
			'warehouse_id'        => 1,
			'payment_method_name' => $order->get_payment_method_title(),
			'invoice_date'        => $order->get_date_paid(),
		);
		foreach ( $order->get_items() as $item ) {
			$pedido_formatted['order_line'][] = array(
				'default_code'       => $item->get_product()->get_sku(),
				'product_uom_qty'    => $item->get_quantity(),
				'price_unit_taxed'   => $item->get_subtotal_tax(),
				'price_unit_untaxed' => $item->get_subtotal(),
			);
		}
		$this->request(
			'/sale_order/import',
			$pedido_formatted
		);
	}

	/**
	 * Send user to odoo
	 *
	 * @param int $user_id the user id.
	 * @return void
	 */
	public static function send_user( $user_id ) {

		$user      = new WP_User( $user_id );
		$user_data = $user->to_array();
		unset( $user_data['user_pass'] );

		$json_user_data = wp_json_encode( $user_data );
		$return         = wp_remote_post(
			self::$url,
			array(
				'headers' => array( 'content-type' => 'application/json' ),
				'body' => $json_user_data,
			)
		);
		if ( is_int( $return ) ) {
			update_user_meta( $user_id, 'id_odoo', $return );
		}
	}

	/**
	 * Check stock to odoo
	 *
	 * @param String     $stock the surrent stock.
	 * @param WC_Product $product the product id.
	 * @return String
	 */
	public function check_odoo_stock( $stock, $product ) {
		require_once ENUCWOODOO_PLUGIN . '/inc/ripcord/ripcord.php';
		$id_odoo = get_post_meta( $product->get_id(), 'id_odoo', true );
		//if ( $id_odoo ) {
			$api        = ripcord::client( $this->url . '/xmlrpc/2/common' );
			$uid        = $api->authenticate( $this->db, $this->user, $this->password, array() );
			$api        = ripcord::client( $this->url . '/xmlrpc/2/object');
			$product_id = $api->execute_kw(
				$this->db,
				$uid,
				$this->password,
				'product.product',
				'search',
				array(
					array(
						'|',
						array(
							'id',
							'=',
							$id_odoo,
						),
						array(
							'default_code',
							'=',
							$product->get_id(),
						),
					),
				)
			);
			$response = $api->execute_kw(
				$this->db,
				$uid,
				$this->password,
				'product.product',
				'read',
				array( $product_id ),
				array( 'fields' => array( 'virtual_available' ) )
			);
			$stock_virtual = $response[0]['virtual_available'];
			//var_dump( $response );
			if ( 0 === $stock_virtual ) {
				$stock = false;
			}
		//}
		//var_dump( $stock );
		return $stock;
	}

}
