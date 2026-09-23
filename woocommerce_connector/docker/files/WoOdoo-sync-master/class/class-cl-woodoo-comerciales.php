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
class Cl_Woodoo_Comerciales extends WP_REST_Posts_Controller {

	/**
	 * Constructor.
	 */
	public function __construct() {
		$this->post_type = 'comerciales';
		$this->namespace = 'woodoo/v1';
		$obj             = get_post_type_object( $this->post_type );
		$this->rest_base = ! empty( $obj->rest_base ) ? $obj->rest_base : $obj->name;

		$this->meta = new WP_REST_Post_Meta_Fields( $this->post_type );

		$this->register_routes();
	}

	/**
	 * Registers the routes for the objects of the controller.
	 *
	 * @since 4.7.0
	 *
	 * @see register_rest_route()
	 */
	public function register_routes() {

		register_rest_route(
			$this->namespace,
			'/' . $this->rest_base,
			array(
				array(
					'methods'             => WP_REST_Server::READABLE,
					'callback'            => array( $this, 'get_items' ),
					'permission_callback' => array( $this, 'get_items_permissions_check' ),
					'args'                => $this->get_collection_params(),
				),
				array(
					'methods'             => WP_REST_Server::CREATABLE,
					'callback'            => array( $this, 'create_item' ),
					'permission_callback' => array( $this, 'create_item_permissions_check' ),
					'args'                => $this->get_endpoint_args_for_item_schema( WP_REST_Server::CREATABLE ),
				),
				'schema' => array( $this, 'get_public_item_schema' ),
			)
		);

		$schema        = $this->get_item_schema();
		$get_item_args = array(
			'context' => $this->get_context_param( array( 'default' => 'view' ) ),
		);
		register_rest_route(
			$this->namespace,
			'/' . $this->rest_base . '/(?P<id>[\d]+)',
			array(
				'args'   => array(
					'id' => array(
						'description' => __( 'Unique identifier for the object.', 'woocommerce' ),
						'type'        => 'integer',
					),
				),
				array(
					'methods'             => WP_REST_Server::READABLE,
					'callback'            => array( $this, 'get_item' ),
					'permission_callback' => array( $this, 'get_item_permissions_check' ),
					'args'                => $get_item_args,
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
							'type'        => 'boolean',
							'default'     => false,
							'description' => __( 'Whether to bypass Trash and force deletion.', 'woocommerce' ),
						),
					),
				),
				'schema' => array( $this, 'get_public_item_schema' ),
			)
		);
	}

	/**
	 * Get id WP to update
	 *
	 * @param stdClass $request the whole request.
	 * @return class
	 */
	public function update_item_permissions_check( $request ) {
		$id_odoo = $request->get_param( 'id_odoo' );
		$id_wp   = get_comercial_id_by_idodoo( $id_odoo );
		$request->set_param( 'id', $id_wp );
		return parent::update_item_permissions_check( $request );
	}
	/**
	 * Get id WP to delete
	 *
	 * @param stdClass $request the whole request.
	 * @return class
	 */
	public function delete_item_permissions_check( $request ) {
		$id_odoo = $request->get_param( 'id_odoo' );
		$id_wp   = get_comercial_id_by_idodoo( $id_odoo );
		$request->set_param( 'id', $id_wp );
		return parent::delete_item_permissions_check( $request );
	}

	/**
	 * Creates a single post.
	 *
	 * @since 4.7.0
	 *
	 * @param WP_REST_Request $request Full details about the request.
	 * @return WP_REST_Response|WP_Error Response object on success, or WP_Error object on failure.
	 */
	public function create_item( $request ) {
		$id_odoo = $request->get_param( 'id_odoo' );
		$id_wp   = get_comercial_id_by_idodoo( $id_odoo );

		if ( false !== $id_wp ) {
			$this->update_item( $request );
			// $error = new WP_Error( 'comercial_exists', 'Comercial exists, don\'t you wanna update?' );
			// wp_send_json_error( $error );
		}

		$request->set_param( 'status', 'publish' );
		$request = $this->prepare_meta( $request );
		return parent::create_item( $request );
	}

	/**
	 * Updates a single post.
	 *
	 * @since 4.7.0
	 *
	 * @param WP_REST_Request $request Full details about the request.
	 * @return WP_REST_Response|WP_Error Response object on success, or WP_Error object on failure.
	 */
	public function update_item( $request ) {
		$id_odoo = $request->get_param( 'id_odoo' );
		$id_wp   = get_comercial_id_by_idodoo( $id_odoo );
		if ( false === $id_wp ) {
			$error = new WP_Error( 'No comercial with this id_odoo' );
			wp_send_json_error( $error );
		}
		$request = $this->prepare_meta( $request );
		$request->set_param( 'id', $id_wp );
		return parent::update_item( $request );
	}

	/**
	 * Deletes a single post.
	 *
	 * @since 4.7.0
	 *
	 * @param WP_REST_Request $request Full details about the request.
	 * @return WP_REST_Response|WP_Error Response object on success, or WP_Error object on failure.
	 */
	public function delete_item( $request ) {
		$id_odoo = $request->get_param( 'id_odoo' );
		$id_wp   = get_comercial_id_by_idodoo( $id_odoo );
		if ( false === $id_wp ) {
			$error = new WP_Error( 'No comercial with this id_odoo' );
			wp_send_json_error( $error );
		}
		$request->set_param( 'id', $id_wp );
		$request->set_param( 'force', true );
		return parent::delete_item( $request );
	}

	/**
	 * Prepare meta_data from fields on root.
	 *
	 * @param WP_REST_Request $request Full details about the request.
	 * @return WP_REST_Response|WP_Error Response object on success, or WP_Error object on failure.
	 */
	public function prepare_meta( $request ) {
		// Add odoo_id to meta_data.
		$meta_data = $request->get_param( 'meta_data' );
		if ( ! is_array( $meta_data ) ) {
			$meta_data = array();
		}
		$meta_data[] = array(
			'key'   => 'id_odoo',
			'value' => $request->get_param( 'id_odoo' ),
		);
		$meta_data[] = array(
			'key'   => 'telefono',
			'value' => $request->get_param( 'telefono' ),
		);
		$meta_data[] = array(
			'key'   => 'extension',
			'value' => $request->get_param( 'extension' ),
		);
		$meta_data[] = array(
			'key'   => 'email',
			'value' => $request->get_param( 'email' ),
		);
		return $request;
	}

}
