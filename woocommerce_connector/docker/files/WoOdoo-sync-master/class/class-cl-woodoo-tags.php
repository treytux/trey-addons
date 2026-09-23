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
class CL_WooDoo_Tags extends WC_REST_Product_Tags_Controller {

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
		/* parent::__construct(); */
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
					'args'                => array_merge(
						$this->get_endpoint_args_for_item_schema( WP_REST_Server::CREATABLE ),
						array(
							'id_odoo' => array(
								'type'        => 'integer',
								'description' => __( 'The Odoo ID', 'woocommerce' ),
								'required'    => true,
							),
						)
					),
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
	 * Check if id_odoo and url id are the same.
	 *
	 * @param WP_REST_Request $request Request instance.
	 */
	public function check_url_consistency( $request ) {
		return;
		if ( $request->get_param( 'id_odoo' ) !== $request->get_param( 'id' ) ) {
			$error = new WP_Error( 'url_mismatch', 'The ID on URL must be the same that id_odoo param' );
			wp_send_json_error( $error );
		}
	}

	/**
	 * Update term meta fields.
	 *
	 * @param WP_Term         $term    Term object.
	 * @param WP_REST_Request $request Request instance.
	 * @return bool|WP_Error
	 *
	 * @since 3.5.5
	 */
	protected function update_term_meta_fields( $term, $request ) {
		if ( $request->get_param( 'id_odoo' ) ) {
			update_term_meta( $term->term_id, 'id_odoo', $request->get_param( 'id_odoo' ) );
		}
		return parent::update_term_meta_fields( $term, $request );
	}

	/**
	 * Change create behaviour
	 *
	 * @param stdClass $request the whole request.
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

		$check_cat = check_if_exists_tag_odoo( $id_odoo );
		if ( null !== $check_cat ) {
			// Check if element exists or translation.
			$id_wp = apply_filters( 'wpml_object_id', $check_cat['term_id'], 'product_tag', false, $lang );
			if ( $id_wp ) {
				return $this->update_item( $request );
				// This product exists and can't create again.
				// $error = new WP_Error( 'product_cat_exists', 'Category exists, don\'t you wanna update?' );
				// wp_send_json_error( $error );
			} else {
				// Product not existing check if translated versions are available.
				// And put the translate_of correct.
				$category_original_id = $check_cat['term_id'];
				$request->set_param( 'translation_of', $check_cat['term_id'] );
			}
		}

		add_action( 'woocommerce_rest_insert_product_tag', array( $this, 'update_term_meta_odoo' ) );
		$created_tax = parent::create_item( $request );
		remove_action( 'woocommerce_rest_insert_product_tag', array( $this, 'update_term_meta_odoo' ) );

		if ( is_wp_error( $created_tax ) ) {
			return $created_tax;
		}

		$data_tax = $created_tax->get_data();

		$category_translated_id = $data_tax['id'];
		$translated_lang        = $lang;

		/* https://wpml.org/wpml-hook/wpml_element_type/ */
		$wpml_element_type = apply_filters( 'wpml_element_type', 'tax_product_tag' );

		/* https://wpml.org/wpml-hook/wpml_element_language_details/ */
		$get_language_args = array(
			'element_id'   => $category_original_id,
			'element_type' => 'tax_product_cat',
		);

		$original_post_language_info = apply_filters( 'wpml_element_language_details', null, $get_language_args );

		$set_language_args = array(
			'element_id'           => $category_translated_id,
			'element_type'         => $wpml_element_type,
			'trid'                 => $original_post_language_info->trid,
			'language_code'        => $translated_lang,
			'source_language_code' => $original_post_language_info->language_code,
		);

		/* https://wpml.org/wpml-hook/wpml_set_element_language_details/ */
		do_action( 'wpml_set_element_language_details', $set_language_args );

		return $created_tax;
	}

	/**
	 * Get id WP to update
	 *
	 * @param stdClass $request the whole request.
	 * @return class
	 */
	public function update_item_permissions_check( $request ) {
		$this->check_url_consistency( $request );
		$id_odoo = $request->get_param( 'id_odoo' );
		$lang    = $request->get_param( 'lang' );
		$id_wp   = get_category_id_by_idodoo( $id_odoo, $lang );
		$request->set_param( 'id', $id_wp['term_id'] );
		return parent::update_item_permissions_check( $request );
	}
	/**
	 * Get id WP to delete
	 *
	 * @param stdClass $request the whole request.
	 * @return class
	 */
	public function delete_item_permissions_check( $request ) {
		$this->check_url_consistency( $request );
		$id_odoo = $request->get_param( 'id_odoo' );
		$lang    = $request->get_param( 'lang' );
		$id_wp   = get_category_id_by_idodoo( $id_odoo, $lang );
		$request->set_param( 'id', $id_wp['term_id'] );
		return parent::delete_item_permissions_check( $request );
	}
	/**
	 * Change update behaviour
	 *
	 * @param stdClass $request the whole request.
	 * @return $request
	 */
	public function update_item( $request ) {
		$id_odoo = $request->get_param( 'id_odoo' );
		$lang    = $request->get_param( 'lang' );
		$id_wp   = get_category_id_by_idodoo( $id_odoo, $lang );
		$request->set_param( 'id', $id_wp['term_id'] );
		return parent::update_item( $request );
	}

	/**
	 * Change delete behaviour
	 *
	 * @param stdClass $request the whole request.
	 * @return $request
	 */
	public function delete_item( $request ) {
		$id_odoo = $request->get_param( 'id_odoo' );
		$lang    = $request->get_param( 'lang' );
		$id_wp   = get_category_id_by_idodoo( $id_odoo, $lang );
		$request->set_param( 'id', $id_wp['term_id'] );
		$request->set_param( 'force', true );
		return parent::delete_item( $request );
	}

}

new CL_WooDoo_Tags();
