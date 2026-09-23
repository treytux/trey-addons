<?php
/**
 * Plugin connector con Odoo.
 *
 * @link        https://tabernawp.com
 * @since       1.0.0
 * @package     Cl_Enuc_WooDoo
 * @author      Carlos Longarela & Adrián Cobo
 * @license     GPL-2.0+
 *
 * @wordpress-plugin
 * Plugin Name:       Plugin connector con Odoo
 * Plugin URI:        https://e-nuc.com
 * Description:       Creación de endpoints.
 * Version:           1.0.0
 * Author:            Carlos Longarela & Adrián Cobo
 * Author URI:        https://tabernawp.com
 * License:           GPL-2.0+
 * License URI:       http://www.gnu.org/licenses/gpl-2.0.txt
 * Text Domain:       cl-enuc-woodoo
 * Domain Path:       /languages
 */

// If this file is called directly, abort.
if ( ! defined( 'WPINC' ) ) {
	die;
}

/**
 * Currently plugin version.
 * Start at version 1.0.0 and use SemVer - https://semver.org
 * Rename this for your plugin and update it as you release new versions.
 */

define( 'CL_ENUC_WOODOO_VERSION', '1.0.0' );
define( 'ENUCWOODOO_PLUGIN', dirname( __FILE__ ) );

/**
 * The code that runs during plugin activation.
 * This action is documented in includes/class-cl-enuc-theme-plugin-activator.php
 */
function activate_cl_enuc_woodoo() {
	require_once plugin_dir_path( __FILE__ ) . 'class/class-cl-enuc-woodoo-activator.php';
	Cl_Enuc_WooDoo_Activator::activate();
}

/**
 * The code that runs during plugin deactivation.
 * This action is documented in includes/class-cl-enuc-theme-plugin-deactivator.php
 */
function deactivate_cl_enuc_woodoo() {
	require_once plugin_dir_path( __FILE__ ) . 'class/class-cl-enuc-woodoo-deactivator.php';
	Cl_Enuc_WooDoo_Deactivator::deactivate();
}

register_activation_hook( __FILE__, 'activate_cl_enuc_theme_plugin' );
register_deactivation_hook( __FILE__, 'deactivate_cl_enuc_theme_plugin' );

require_once ENUCWOODOO_PLUGIN . '/inc/functions.general.php';

/**
 * Function that loads all overriding classes
 *
 * @return void
 */
function cl_woodoo_extend_classes() {
	require_once ENUCWOODOO_PLUGIN . '/class/class-cl-woodoo-comerciales.php';
	require_once ENUCWOODOO_PLUGIN . '/class/class-cl-woodoo-users.php';
	new Cl_Woodoo_Comerciales();
	new Cl_Woodoo_Users();

}
add_action( 'rest_api_init', 'cl_woodoo_extend_classes', 99999 );

/**
 * Function that loads all overriding woo classes
 *
 * @return void
 */
function cl_woodoo_extend_wo_classes() {
	if ( class_exists( 'woocommerce' ) ) {
		require_once ENUCWOODOO_PLUGIN . '/class/class-cl-woodoo-products.php';
		require_once ENUCWOODOO_PLUGIN . '/class/class-cl-woodoo-products-attributes.php';
		require_once ENUCWOODOO_PLUGIN . '/class/class-cl-woodoo-products-variations.php';
		require_once ENUCWOODOO_PLUGIN . '/class/class-cl-woodoo-categories.php';
		require_once ENUCWOODOO_PLUGIN . '/class/class-cl-woodoo-tags.php';
		require_once ENUCWOODOO_PLUGIN . '/class/class-cl-woodoo-marcas.php';
		new CL_WooDoo_Products();
		new CL_WooDoo_Categories();
		new Cl_Woodoo_Products_Attributes();
		new CL_WooDoo_Products_Variations();
		new CL_WooDoo_Marcas();
	}
}
add_action( 'plugins_loaded', 'cl_woodoo_extend_wo_classes', 99999 );

/**
 * Filter to tell wpml is a woocommerce request.
 *
 * @param bool $woocommerce previous filter value.
 * @return bool
 */
function check_woodoo_api( $woocommerce ) {
	$rest_prefix = trailingslashit( rest_get_url_prefix() );
	$woodoo_rest = ( false !== strpos( $_SERVER['REQUEST_URI'], $rest_prefix . 'woodoo' ) );
	return $woocommerce || $woodoo_rest;
}
add_filter( 'woocommerce_is_rest_api_request', 'check_woodoo_api' );
add_filter( 'woocommerce_rest_is_request_to_rest_api', 'check_woodoo_api' );

/**
 * Add ID Odoo by variation.
 *
 * @param string $loop the current variation number.
 * @param array  $variation_data the variation data.
 * @param object $variation the current variation object.
 * @return void
 */
function cl_add_custom_field_to_variations( $loop, $variation_data, $variation ) {
	woocommerce_wp_text_input(
		array(
			'id' => 'id_odoo[' . $loop . ']',
			'class' => 'short',
			'label' => __( 'ID Odoo', 'woocommerce' ),
			'wrapper_class' => 'form-field form-row form-row-first',
			'value' => get_post_meta( $variation->ID, 'id_odoo', true )
		)
	);
}
add_action( 'woocommerce_variation_options_pricing', 'cl_add_custom_field_to_variations', 10, 3 );

/**
 * Send order object to odoo.
 *
 * @param int $order_id the order id.
 */
function send_order_to_odoo( $order_id ) {
	require_once ENUCWOODOO_PLUGIN . '/class/class-cl-enuc-sendtoodoo.php';
	$order_json = new CL_SendtoOdoo();
	$order_json->send_order( $order_id );
}
add_action( 'woocommerce_new_order', 'send_order_to_odoo', 10, 1 );

/**
 * Send order object to odoo.
 *
 * @param int $user_id the user id.
 */
function send_customer_to_odoo( $user_id ) {
	$user_data = get_userdata( $user_id );
	if ( $user_data ) {
		require_once ENUCWOODOO_PLUGIN . '/class/class-cl-enuc-sendtoodoo.php';
		$order_json = new CL_SendtoOdoo();
		$order_json->send_user( $user_data );
	}
}
add_action( 'user_register', 'send_customer_to_odoo', 10, 1 );

/**
 * Override account links to odoo
 *
 * @param string $url
 * @param string $endpoint
 * @param string $value
 * @param string $permalink
 * @return void
 */
function cl_change_my_account_links( $url, $endpoint, $value, $permalink ) {
	global $current_user;

	if ( $current_user ) {
    	$permission = get_user_meta( $current_user->ID, 'token_odoo', true );
	}
	$url_odoo = $url;
	if ( $permission ) {
		$url_odoo = 'http://futurnet.treytux.com:8069/token/' . $permission;
	}
	switch ( $endpoint ) {
		/*case 'edit-address':
			$url = 'https://enuc.odoo.com';
			break;
		case 'payment-methods':
			$url = 'https://enuc.odoo.com';
			break;*/
		case 'orders':
		case 'edit-account':
			$url = $url_odoo;
			break;
	}
	return $url;
}
add_filter( 'woocommerce_get_endpoint_url', 'cl_change_my_account_links', 9999, 4 );

function cl_remove_my_account_links( $menu_links ) {

	// unset( $menu_links['edit-address'] ); // Addresses
	// unset( $menu_links['dashboard'] ); // Remove Dashboard
	// unset( $menu_links['payment-methods'] ); // Remove Payment Methods
	// unset( $menu_links['orders'] ); // Remove Orders
	unset( $menu_links['downloads'] ); // Disable Downloads
	// unset( $menu_links['edit-account'] ); // Remove Account details tab

	return $menu_links;
}
add_filter( 'woocommerce_account_menu_items', 'cl_remove_my_account_links' );

/**
 * Add meta box to members edit page
 *
 * @param string $screen_id the current screen.
 * @param string $role the current role.
 * @return void
 */
function add_meta_box_member_odoo_id( $screen_id, $role = '' ) {

	// If role isn't editable, bail.
	if ( $role && ! members_is_role_editable( $role ) )
		return;

	// Add the meta box.
	add_meta_box(
		'mrh_role_member_odoo_id',
		esc_html__( 'ID Odoo', 'cl-woodoo-sync' ),
		'meta_box_members_odoo_id',
		'members_page_roles',
		'side',
		'core'
	);
}
add_action( 'add_meta_boxes_members_page_roles', 'add_meta_box_member_odoo_id', 10, 2 );

/**
 * Show input to put id_odoo at member
 *
 * @return void
 */
function meta_box_members_odoo_id() {
	global $wpdb;
	$current_role = get_role( members_sanitize_role( $_GET['role'] ) );
	$sql     = $wpdb->prepare( 'SELECT o.option_name FROM ' . $wpdb->options . ' o WHERE o.option_value = %s AND o.option_name LIKE %s LIMIT 1', $current_role->name, 'member_odoo_id_%' );
	$results = $wpdb->get_results( $sql, ARRAY_A ); // phpcs:ignore Standard.Category.SniffName.ErrorCode: unprepared SQL OK.
	$value = explode( 'member_odoo_id_', $results[0]['option_name'] );
	$val = isset( $value[1] ) ? $value[1] : '';
	?>
		<p>
			<input type="text" name="member_odoo_id_<?php echo esc_attr( $current_role->name ); ?>" id="member_odoo_id_<?php echo esc_attr( $current_role->name ); ?>" class="widefat" value="<?php echo esc_html( $val ); ?>" />
		</p>
	<?php
}

/**
 * Add ID Odoo to role member.
 *
 * @param string $role the current role.
 * @return void
 */
function add_meta_idodoo_to_role( $role ) {
	global $wpdb;
	check_admin_referer( 'edit_role', 'members_edit_role_nonce' );
	if ( isset( $_POST[ 'member_odoo_id_' . $role ] ) ) {
		$wpdb->query( $wpdb->prepare( 'DELETE FROM ' . $wpdb->options . ' WHERE option_value = %s AND option_name LIKE %s', $role, 'member_odoo_id_%' ) );
		update_option( 'member_odoo_id_' . $_POST[ 'member_odoo_id_' . $role ], $role );
	}
}
add_action( 'members_role_updated', 'add_meta_idodoo_to_role' );


/**
 * Undocumented function
 *
 * @param [type] $stock Current status.
 * @param [type] $product Current product.
 * @return String
 */
function enuc_check_odoo_stock( $stock, $product ) {
	require_once ENUCWOODOO_PLUGIN . '/class/class-cl-enuc-sendtoodoo.php';
	$odoo = new CL_SendtoOdoo();
	return $odoo->check_odoo_stock( $stock, $product );
}
add_filter( 'woocommerce_product_is_in_stock', 'enuc_check_odoo_stock', 10, 2 );
