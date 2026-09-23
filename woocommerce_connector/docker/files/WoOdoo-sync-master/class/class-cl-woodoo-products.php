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
class CL_WooDoo_Products extends WC_REST_Products_Controller {

	/**
	 * Endpoint namespace.
	 *
	 * @var string
	 */
	public $namespace = 'woodoo/v1';

	/**
	 * Function construct.
	 */
	public function __construct() {
		add_action( 'rest_api_init', array( $this, 'register_rest_routes' ), 8 );
	}

	/**
	 * Register the routes for products.
	 */
	public function register_rest_routes() {
		register_rest_route(
			$this->namespace,
			'/' . $this->rest_base,
			array(
				array(
					'methods'             => WP_REST_Server::CREATABLE,
					'callback'            => array( $this, 'create_item' ),
					'permission_callback' => array( $this, 'create_item_permissions_check' ),
					'args'                => $this->get_endpoint_args_for_item_schema( WP_REST_Server::CREATABLE ),
				),
				'schema' => array( $this, 'get_public_item_schema' ),
			)
		);
		register_rest_route(
			$this->namespace,
			'/' . $this->rest_base . '/(?P<id>[\d]+)',
			array(
				'args'   => array(
					'id' => array(
						'description' => __( 'Unique identifier for the resource.', 'woocommerce' ),
						'type'        => 'integer',
					),
				),
				array(
					'methods'             => WP_REST_Server::EDITABLE,
					'callback'            => array( $this, 'update_item' ),
					'permission_callback' => array( $this, 'update_item_permissions_check' ),
					'args'                => $this->get_endpoint_args_for_item_schema( WP_REST_Server::EDITABLE ),
				),
				array(
					'methods'             => WP_REST_Server::DELETABLE,
					'callback'            => array( $this, 'delete_item' ),
					'permission_callback' => array( $this, 'delete_item_permissions_check' ),
					'args'                => array(
						'force' => array(
							'default'     => false,
							'description' => __( 'Whether to bypass trash and force deletion.', 'woocommerce' ),
							'type'        => 'boolean',
						),
					),
				),
				'schema' => array( $this, 'get_public_item_schema' ),
			)
		);
	}

	/**
	 * Change create behaviour
	 *
	 * @param WP_REST_Request $request the whole request.
	 * @return $request
	 */
	public function create_item( $request ) {
		$id_odoo = $request->get_param( 'id_odoo' );
		$lang    = $request->get_param( 'lang' );

		// Check if id_odoo and lang are set.
		if ( ! $id_odoo || ! $lang ) {
			$error = new WP_Error( 'required_fields', 'Must send lang and id_odoo.' );
			wp_send_json_error( $error );
		}

		$check_product = check_if_exists_product_odoo( $id_odoo );
		if ( null !== $check_product ) {
			// Check if element exists or translation.
			$id_wp = apply_filters( 'wpml_object_id', $check_product['post_id'], 'product', false, $lang );
			if ( $id_wp ) {
				return $this->update_item( $request );
				// This product exists and can't create again.
				// $error = new WP_Error( 'product_exists', 'Product exists, don\'t you wanna update?' );
				// wp_send_json_error( $error );
			} else {
				// Product not existing check if translated versions are available.
				// And put the translate_of correct.
				$request->set_param( 'translation_of', $check_product['post_id'] );
			}
		}

		// Add odoo_id to meta_data.
		$meta_data = $request->get_param( 'meta_data' );
		if ( ! is_array( $meta_data ) ) {
			$meta_data = array();
		}
		$meta_data[] = array(
			'key'   => 'id_odoo',
			'value' => $id_odoo,
		);

		$meta_data = $request->set_param( 'meta_data', $meta_data );

		$request = $this->change_cats_and_relateds( $request );

		if ( $request->get_param( 'attributes' ) ) {
			$attributes = $request->get_param( 'attributes' );
			foreach ( $attributes as $index => $attr ) {
				$attr_id = wc_attribute_taxonomy_id_by_name( $attr['slug'] );
				$attributes[ $index ]['id'] = $attr_id;
			}
			$request->set_param( 'attributes', $attributes );
		}

		$item_created = parent::create_item( $request );

		$wp_id = $item_created->get_data();

		if ( $request->get_param( 'marcas' ) ) {
			$this->add_marcas( $wp_id['id'], $request->get_param( 'marcas' ) );
		}
		if ( $request->get_param( 'bulk_prices' ) ) {
			$this->delete_bulk_prices( $wp_id['id'] );
			$this->add_bulk_prices( $wp_id['id'], $request->get_param( 'bulk_prices' ) );
		}

		return $item_created;

	}

	/**
	 * Change update behaviour
	 *
	 * @param WP_REST_Request $request the whole request.
	 * @return $request
	 */
	public function update_item( $request ) {
		$id_odoo       = $request->get_param( 'id_odoo' );
		$lang          = $request->get_param( 'lang' );
		$check_product = check_if_exists_product_odoo( $id_odoo );
		$id_wp         = apply_filters( 'wpml_object_id', $check_product['post_id'], 'product', false, $lang );

		if ( ! isset( $id_wp ) ) {
			$error = new WP_Error( 'Must create "' . $lang . '" language first for this product.' );
			wp_send_json_error( $error );
		}
		$request->set_param( 'id', $id_wp );
		$request->set_param( 'translation_of', $check_product['post_id'] );

		$request = $this->change_cats_and_relateds( $request );

		if ( $request->get_param( 'marcas' ) ) {
			wp_set_object_terms( $id_wp, null, 'marcas' );
			$this->add_marcas( $id_wp, $request->get_param( 'marcas' ) );
		}

		if ( $request->get_param( 'attributes' ) ) {
			$attributes = $request->get_param( 'attributes' );
			foreach ( $attributes as $index => $attr ) {
				$attr_id = wc_attribute_taxonomy_id_by_name( $attr['slug'] );
				$attributes[ $index ]['id'] = $attr_id;
			}
			$request->set_param( 'attributes', $attributes );
		}

		if ( $request->get_param( 'bulk_prices' ) ) {
			$this->delete_bulk_prices( $id_wp );
			$this->add_bulk_prices( $id_wp, $request->get_param( 'bulk_prices' ) );
		}
		return parent::update_item( $request );
	}

	/**
	 * Change delete behaviour
	 *
	 * @param WP_REST_Request $request the whole request.
	 * @return $request
	 */
	public function delete_item( $request ) {
		$id_odoo       = $request->get_param( 'id_odoo' );
		$lang          = $request->get_param( 'lang' );
		$check_product = check_if_exists_product_odoo( $id_odoo );
		$id_wp         = apply_filters( 'wpml_object_id', $check_product['post_id'], 'product', false, $lang );
		if ( ! $id_wp ) {
			$error = new WP_Error( 'This product on this language not exists.' );
			wp_send_json_error( $error );
		}
		$request->set_param( 'id', $id_wp );
		$request->set_param( 'force', true );

		// TODO: Delete discounts by product.
		$this->delete_bulk_prices( $id_wp );
		return parent::delete_item( $request );
	}

	/**
	 * Change categories and relateds ids.
	 *
	 * @param WP_REST_Request $request the whole request.
	 * @return $request
	 */
	public function change_cats_and_relateds( $request ) {
		// Category transform to id wc.
		$lang = $request->get_param( 'lang' );
		if ( $request->get_param( 'categories' ) ) {
			$new_cats   = array();
			$categories = $request->get_param( 'categories' );
			foreach ( $categories as $ct ) {
				$cat_id     = get_category_id_by_idodoo( $ct['id'], $lang );
				$new_cats[] = array( 'id' => $cat_id['term_id'] );
			}
			$request->set_param( 'categories', $new_cats );
		}
		// Tags transform to id wc.
		if ( $request->get_param( 'tags' ) ) {
			$new_cats   = array();
			$categories = $request->get_param( 'tags' );
			foreach ( $categories as $ct ) {
				$cat_id     = get_category_id_by_idodoo( $ct['id'], $lang );
				$new_cats[] = array( 'id' => $cat_id['term_id'] );
			}
			$request->set_param( 'tags', $new_cats );
		}
		// Cross Selll get id by id_odoo.
		if ( $request->get_param( 'cross_sell_ids' ) ) {
			$new_cross = array();
			$cross     = $request->get_param( 'cross_sell_ids' );
			foreach ( $cross as $ct ) {
				$cross_id    = get_product_id_by_idodoo( $ct, $lang );
				$new_cross[] = $cross_id['post_id'];
			}
			$request->set_param( 'cross_sell_ids', $new_cross );
		}

		// Upsell get id by id_odoo.
		if ( $request->get_param( 'upsell_ids' ) ) {
			$new_upsells = array();
			$upsell      = $request->get_param( 'upsell_ids' );
			foreach ( $categories as $ct ) {
				$cat_id        = get_product_id_by_idodoo( $ct, $lang );
				$new_upsells[] = $cat_id['post_id'];
			}
			$request->set_param( 'upsell_ids', $new_upsells );
		}

		return $request;
	}

	/**
	 * Transform input request to prices lines
	 *
	 * @param int   $id_wp the id of the product.
	 * @param array $marcas array with the marcas.
	 * @return void
	 */
	private function add_marcas( $id_wp, $marcas ) {
		$marcas_set = '';
		foreach ( $marcas as $marca ) {
			$marca_id    = get_marca_id_by_idodoo( $marca['id'] );
			$marcas_set .= $marca_id['term_id'] . ',';
		}
		wp_set_post_terms( $id_wp, $marcas_set, 'marcas' );
	}

	/**
	 * Transform input request to prices lines
	 *
	 * @param int   $id_wp the id of the product.
	 * @param array $prices array with the prices.
	 * @return void
	 */
	private function add_bulk_prices( $id_wp, $prices ) {

		// For each price roles create rule.
		foreach ( $prices[0] as $role_odoo => $rules ) {

			$role = get_option( 'member_odoo_id_' . $role_odoo );

			if ( $role ) {
				$post        = array(
					'post_title'  => 'Producto ID ' . $id_wp . ' (' . $role . ')',
					'post_status' => 'publish',
					'post_type'   => 'ywdpd_discount',
				);
				$discount_id = wp_insert_post( $post );

				$post_meta = array(
					'_post_id_ref'                    => $id_wp,
					'_key'                            => uniqid(),
					'_discount_type'                  => 'pricing',
					'_active'                         => 1,
					'_priority'                       => 2,
					'_discount_mode'                  => 'bulk',
					'_show_table_price'               => 1,
					'_show_in_loop'                   => 1,
					'_quantity_based'                 => 'single_product',
					'_apply_to'                       => 'products_list',
					'_apply_to_products_list'         => array(
						$id_wp,
					),
					'_n_items_in_cart'                => array(
						'condition' => '>',
						'n_items'   => 1,
					),
					'_apply_adjustment'               => 'same_product',
					'_apply_with_other_rules'         => 0,
					'_apply_on_sale'                  => 0,
					'_disable_with_other_coupon'      => 0,
					'_apply_adjustment_products_list' => array(
						$id_wp,
					),
					'_schedule_from'                  => '',
					'_schedule_to'                    => '',
					'_amount_gift_product_allowed'    => '',
					'_table_note_apply_to'            => '',
					'_table_note_adjustment_to'       => '',
					'_table_note'                     => '',
					'so-rule'                         => array(
						'purchase'        => '',
						'receive'         => '',
						'type_discount'   => 'percentage',
						'discount_amount' => '',
					),
				);

				if ( 'everyone' === $role ) {
					$post_meta['_user_rules'] = 'everyone';
				} else {
					$post_meta['_user_rules']           = 'role_list';
					$post_meta['_user_rules_role_list'] = array( $role );
				}

				// hecho con query a saco para mejorar rendimiento y evitar 18 update_post_meta.
				global $wpdb;
				$values = '';
				$a      = 0;
				foreach ( $post_meta as $key => $val ) {
					$a++;
					if ( $a > 1 ) {
						$values .= ',';
					}
					$values .= '(' . $discount_id . ",'" . $key . "','" . maybe_serialize( $val ) . "')";
				}
				$sql = 'INSERT INTO ' . $wpdb->postmeta . ' (post_id,meta_key,meta_value) VALUES ' . $values;
				$wpdb->query( $sql );
				array_unshift( $rules, '' );
				unset( $rules[0] );
				update_post_meta( $discount_id, 'rules', $rules );
			}
		}
		// Remove yith cache discount transient.
		delete_transient( 'ywdpd_discount_ids_cart' );
		delete_transient( 'ywdpd_discount_ids_pricing' );
	}

	/**
	 * Delete the bulk prices from the product
	 *
	 * @param int $id_wp the id of the product.
	 * @return void
	 */
	private function delete_bulk_prices( $id_wp ) {
		$query = new WP_Query(
			array(
				'post_type'      => 'ywdpd_discount',
				'meta_key'       => '_post_id_ref',
				'meta_value'     => $id_wp,
				'posts_per_page' => -1,
			)
		);
		if ( $query->have_posts() ) {
			while ( $query->have_posts() ) {
				$query->the_post();
				wp_delete_post( get_the_ID(), true );
			}
		}
		// Remove yith cache discount transient.
		delete_transient( 'ywdpd_discount_ids_cart' );
		delete_transient( 'ywdpd_discount_ids_pricing' );
	}
}
