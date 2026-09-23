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
class Cl_Woodoo_Users extends WP_REST_Users_Controller {

	/**
	 * Constructor.
	 *
	 * @since 4.7.0
	 */
	public function __construct() {
		$this->namespace = 'woodoo/v1';
		$this->rest_base = 'users';

		$this->meta = new WP_REST_User_Meta_Fields();
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

		register_rest_route(
			$this->namespace,
			'/' . $this->rest_base . '/(?P<id>[\d]+)',
			array(
				'args'   => array(
					'id' => array(
						'description' => __( 'Unique identifier for the user.' ),
						'type'        => 'integer',
					),
				),
				array(
					'methods'             => WP_REST_Server::READABLE,
					'callback'            => array( $this, 'get_item' ),
					'permission_callback' => array( $this, 'get_item_permissions_check' ),
					'args'                => array(
						'context' => $this->get_context_param( array( 'default' => 'view' ) ),
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
						'id_odoo'  => array(
							'type'     => 'integer',
							'required' => true,
						),
						'force'    => array(
							'type'        => 'boolean',
							'default'     => false,
							'description' => __( 'Required to be true, as users do not support trashing.' ),
						),
						'reassign' => array(
							'type'              => 'integer',
							'description'       => __( 'Reassign the deleted user\'s posts and links to this user ID.' ),
							'required'          => false,
							'sanitize_callback' => array( $this, 'check_reassign' ),
						),
					),
				),
				'schema' => array( $this, 'get_public_item_schema' ),
			)
		);
	}

	/**
	 * Create user
	 *
	 * @param WP_REST_Request $request the whole request.
	 * @return $request
	 */
	public function create_item( $request ) {

		$id_odoo = $request->get_param( 'id_odoo' );

		// Check if id_odoo and lang are set.
		if ( ! $id_odoo ) {
			$error = new WP_Error( 'required_fields', 'Must send id_odoo.' );
			wp_send_json_error( $error );
		}

		$id_wp = get_user_id_by_idodoo( $id_odoo );

		if ( false !== $id_wp ) {
			return $this->update_item( $request );
			// $error = new WP_Error( 'user_exists', 'User exists, don\'t you wanna update?' );
			// wp_send_json_error( $error );
		}

		if ( $request->get_param( 'roles' ) ) {
			$roles   = $request->get_param( 'roles' );
			$roleswp = array();
			foreach ( $roles as $r ) {
				$roleswp[] = get_option( 'member_odoo_id_' . $r );
			}

			if ( ! in_array( 'customer', $roleswp, true ) && ! in_array( 'distribuidor', $roleswp, true ) ) {
				$error = new WP_Error( 'role_not_match', 'Role must be customer or partner' );
				wp_send_json_error( $error );
			}
			$request->set_param( 'roles', $roleswp );

		} else {
			$roles = array( 'customer' );
			$request->set_param( 'roles', $roles );
		}

		if ( $request->get_param( 'idodoo_comercial' ) ) {
			$id_comercial = $request->get_param( 'idodoo_comercial' );
			$id_comercial = get_comercial_id_by_idodoo( $id_comercial );
			$request->set_param( 'rel_id_comercial', $id_comercial );
		}

		$img_uploaded = $this->upload_image_distribuidor( $request );
		$request->set_param( 'logo_partner', $img_uploaded );

		$user_created = parent::create_item( $request );

		$customer = new WC_Customer( $id_wp );
		$customer = $this->set_meta_customer( $customer, $request );
		$customer->save();
		return $customer;
	}

	/**
	 * Create user
	 *
	 * @param WP_REST_Request $request the whole request.
	 * @return $request
	 */
	public function update_item( $request ) {
		$id_odoo = $request->get_param( 'id_odoo' );
		$id_wp   = get_user_id_by_idodoo( $id_odoo );

		if ( false === $id_wp ) {
			$error = new WP_Error( 'user_not_exists', 'User not exist' );
			wp_send_json_error( $error );
		}
		$request->set_param( 'id', $id_wp );
		if ( $request->get_param( 'roles' ) ) {
			$roles   = $request->get_param( 'roles' );
			$roleswp = array();
			foreach ( $roles as $r ) {
				$roleswp[] = get_option( 'member_odoo_id_' . $r );
			}

			if ( ! in_array( 'customer', $roleswp, true ) && ! in_array( 'distribuidor', $roleswp, true ) ) {
				$error = new WP_Error( 'role_not_match', 'Role must be customer or partner' );
				wp_send_json_error( $error );
			}
			$request->set_param( 'roles', $roleswp );

		} else {
			$roles = array( 'customer' );
			$request->set_param( 'roles', $roles );
		}

		if ( $request->get_param( 'idodoo_comercial' ) ) {
			$id_comercial = $request->get_param( 'idodoo_comercial' );
			$id_comercial = get_comercial_id_by_idodoo( $id_comercial );
			$request->set_param( 'rel_id_comercial', $id_comercial );
		}

		$customer = new WC_Customer( $id_wp );

		$customer = $this->set_meta_customer( $customer, $request );
		$customer->save();

		$img_uploaded = $this->upload_image_distribuidor( $request );
		$request->set_param( 'logo_partner', $img_uploaded );

		return parent::update_item( $request );
	}

	/**
	 * Set the customer billing and address
	 *
	 * @param WC_Customer     $customer The customer object.
	 * @param WC_REST_Request $request The coming request.
	 * @return $customer
	 */
	public function set_meta_customer( $customer, $request ) {
		// Customer first name.
		if ( isset( $request['first_name'] ) ) {
			$customer->set_first_name( wc_clean( $request['first_name'] ) );
		}

		// Customer last name.
		if ( isset( $request['last_name'] ) ) {
			$customer->set_last_name( wc_clean( $request['last_name'] ) );
		}

		// Customer billing address.
		if ( isset( $request['billing'] ) ) {
			foreach ( $request['billing'] as $field => $value ) {
				if ( is_callable( array( $customer, "set_billing_{$field}" ) ) ) {
					$customer->{"set_billing_{$field}"}( $value );
				}
			}
		}

		// Customer shipping address.
		if ( isset( $request['shipping'] ) ) {
			foreach ( $request['shipping'] as $field => $value ) {
				if ( is_callable( array( $customer, "set_shipping_{$field}" ) ) ) {
					$customer->{"set_shipping_{$field}"}( $value );
				}
			}
		}
		return $customer;
	}

	/**
	 * Update item
	 *
	 * @param WP_Request $request the coming request.
	 * @return $request
	 */
	public function update_item_permissions_check( $request ) {
		$id_odoo = $request->get_param( 'id_odoo' );
		$id_wp   = get_user_id_by_idodoo( $id_odoo );

		if ( false === $id_wp ) {
			$error = new WP_Error( 'user_not_exists', 'User not exist' );
			wp_send_json_error( $error );
		}
		$request->set_param( 'id', $id_wp );

		return parent::delete_item_permissions_check( $request );
	}

	/**
	 * Delete item
	 *
	 * @param WP_Request $request the coming request.
	 * @return $request
	 */
	public function delete_item_permissions_check( $request ) {
		$id_odoo = $request->get_param( 'id_odoo' );
		$id_wp   = get_user_id_by_idodoo( $id_odoo );

		if ( false === $id_wp ) {
			$error = new WP_Error( 'user_not_exists', 'User not exist' );
			wp_send_json_error( $error );
		}
		$request->set_param( 'id', $id_wp );

		$admin_email = get_option( 'admin_email' );
		$user        = get_user_by( 'email', $admin_email );
		$request->set_param( 'reassign', $user->ID );
		return parent::delete_item_permissions_check( $request );
	}

	/**
	 * Delete item
	 *
	 * @param WP_Request $request the coming request.
	 * @return $request
	 */
	public function delete_item( $request ) {
		$id_odoo = $request->get_param( 'id_odoo' );
		$id_wp   = get_user_id_by_idodoo( $id_odoo );

		if ( false === $id_wp ) {
			$error = new WP_Error( 'user_not_exists', 'User not exist' );
			wp_send_json_error( $error );
		}
		$request->set_param( 'id', $id_wp );

		$admin_email = get_option( 'admin_email' );
		$user        = get_user_by( 'email', $admin_email );
		$request->set_param( 'reassign', $user->ID );
		$request->set_param( 'force', true );
		return parent::delete_item( $request );
	}

	/**
	 * Función para hacer upload del logo
	 *
	 * @param WC_REST_Request $request the coming request.
	 * @return void
	 */
	public function upload_image_distribuidor( $request ) {
		if ( isset( $request['logo_partner'] ) ) {
			$upload = wc_rest_upload_image_from_url( esc_url_raw( $request['logo_partner'] ) );

			if ( is_wp_error( $upload ) ) {
				if ( ! apply_filters( 'woocommerce_rest_suppress_image_upload_error', false, $upload, $product->get_id(), $images ) ) {
					throw new WC_REST_Exception( 'user_distribuidor_image_upload_error', $upload->get_error_message(), 400 );
				}
			}

			$attachment_id = wc_rest_set_uploaded_image_as_attachment( $upload );
			return $attachment_id;
		}
	}
}
