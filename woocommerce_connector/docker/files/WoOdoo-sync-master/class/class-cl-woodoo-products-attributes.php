<?php
/**
 * API SEND TO ODOO *
 * Customer create
 * Order create
 *
 * @package WooDoo_Customers
 */

/**
 * Class to hook on create users and save id_odoo.
 */
class Cl_Woodoo_Products_Attributes extends WC_REST_Product_Attributes_Controller {

	/**
	 * Endpoint namespace.
	 *
	 * @var string
	 */
	protected $namespace = 'woodoo/v1';


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
					'args'                => array_merge( $this->get_endpoint_args_for_item_schema( WP_REST_Server::CREATABLE ), array(
						'name' => array(
							'description' => __( 'Name for the resource.', 'woocommerce' ),
							'type'        => 'string',
							'required'    => true,
						),
					) ),
				),
				'schema' => array( $this, 'get_public_item_schema' ),
			)
		);

		register_rest_route(
			$this->namespace,
			'/' . $this->rest_base . '/(?P<id>[\S]+)',
			array(
				'args'   => array(
					'id' => array(
						'description' => __( 'Unique identifier for the resource.', 'woocommerce' ),
						'type'        => 'string',
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
	 * @param stdClass $request the whole request.
	 * @return $request
	 */
	public function create_item( $request ) {
		$slug = $request->get_param( 'slug' );

		// Check if id_odoo are set.
		if ( ! $slug ) {
			$error = new WP_Error( 'required_fields', 'Must send slug.' );
			wp_send_json_error( $error );
		}

		$check_cat = check_if_exists_attribute_odoo( $slug );

		if ( null !== $check_cat ) {
			// This product exists and can't create again.
			$this->update_item( $request );
			// $error = new WP_Error( 'attribute_exists', 'Attribute exists, don\'t you wanna update?' );
			// wp_send_json_error( $error );
		}
		$created_tax = parent::create_item( $request );

		return $created_tax;
	}

	/**
	 * Get id WP to update
	 *
	 * @param stdClass $request the whole request.
	 * @return class
	 */
	public function update_item_permissions_check( $request ) {
		$slug  = $request->get_param( 'slug' );
		$id_wp = get_attribute_id_by_slug( $slug );
		$request->set_param( 'id', $id_wp['attribute_id'] );
		return parent::update_item_permissions_check( $request );
	}
	/**
	 * Get id WP to delete
	 *
	 * @param stdClass $request the whole request.
	 * @return class
	 */
	public function delete_item_permissions_check( $request ) {
		$slug  = $request->get_param( 'slug' );
		$id_wp = get_attribute_id_by_slug( $slug );
		$request->set_param( 'id', $id_wp['attribute_id'] );
		return parent::delete_item_permissions_check( $request );
	}
	/**
	 * Change update behaviour
	 *
	 * @param stdClass $request the whole request.
	 * @return $request
	 */
	public function update_item( $request ) {
		$slug  = $request->get_param( 'slug' );
		$id_wp = get_attribute_id_by_slug( $slug );
		$request->set_param( 'id', $id_wp['attribute_id'] );
		return parent::update_item( $request );
	}

	/**
	 * Change delete behaviour
	 *
	 * @param stdClass $request the whole request.
	 * @return $request
	 */
	public function delete_item( $request ) {
		$slug  = $request->get_param( 'slug' );
		$id_wp = get_attribute_id_by_slug( $slug );
		$request->set_param( 'id', $id_wp['attribute_id'] );
		$request->set_param( 'force', true );
		return parent::delete_item( $request );
	}

}
