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
class CL_WooDoo_Marcas extends WC_REST_Terms_Controller {

	/**
	 * Endpoint namespace.
	 *
	 * @var string
	 */
	public $namespace = 'woodoo/v1';

	/**
	 * Route base.
	 *
	 * @var string
	 */
	protected $rest_base = 'products/marcas';

	/**
	 * Taxonomy.
	 *
	 * @var string
	 */
	protected $taxonomy = 'marcas';

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
	 * Change create behaviour
	 *
	 * @param stdClass $request the whole request.
	 * @return $request
	 */
	public function create_item( $request ) {
		$id_odoo = $request->get_param( 'id_odoo' );

		// Check if id_odoo are set.
		if ( ! $id_odoo ) {
			$error = new WP_Error( 'required_fields', 'Must send id_odoo.' );
			wp_send_json_error( $error );
		}

		$check_cat = check_if_exists_marca_odoo( $id_odoo );

		if ( null !== $check_cat ) {
			// This product exists and can't create again.
			$this->update_item( $request );
			// $error = new WP_Error( 'marca_exists', 'Marca exists, don\'t you wanna update?' );
			// wp_send_json_error( $error );
		}

		add_action( 'woocommerce_rest_insert_marca', array( $this, 'update_term_meta_odoo' ) );
		$created_tax = parent::create_item( $request );
		remove_action( 'woocommerce_rest_insert_marca', array( $this, 'update_term_meta_odoo' ) );

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
		$id_wp   = get_marca_id_by_idodoo( $id_odoo );
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
		$id_wp   = get_marca_id_by_idodoo( $id_odoo );
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
		$id_wp   = get_marca_id_by_idodoo( $id_odoo );
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
		$id_wp   = get_marca_id_by_idodoo( $id_odoo );
		$request->set_param( 'id', $id_wp['term_id'] );
		$request->set_param( 'force', true );
		return parent::delete_item( $request );
	}

	/**
	 * Prepare a single product marca output for response.
	 *
	 * @param WP_Term         $item    Term object.
	 * @param WP_REST_Request $request Request instance.
	 * @return WP_REST_Response
	 */
	public function prepare_item_for_response( $item, $request ) {
		// Get category display type.
		$display_type = get_term_meta( $item->term_id, 'display_type', true );

		// Get category order.
		$menu_order = get_term_meta( $item->term_id, 'order', true );

		$data = array(
			'id'          => (int) $item->term_id,
			'name'        => $item->name,
			'slug'        => $item->slug,
			'parent'      => (int) $item->parent,
			'description' => $item->description,
			'display'     => $display_type ? $display_type : 'default',
			'image'       => null,
			'menu_order'  => (int) $menu_order,
			'count'       => (int) $item->count,
		);

		// Get category image.
		$image_id = get_term_meta( $item->term_id, 'thumbnail_id', true );
		if ( $image_id ) {
			$attachment = get_post( $image_id );

			$data['image'] = array(
				'id'            => (int) $image_id,
				'date_created'  => wc_rest_prepare_date_response( $attachment->post_date_gmt ),
				'date_modified' => wc_rest_prepare_date_response( $attachment->post_modified_gmt ),
				'src'           => wp_get_attachment_url( $image_id ),
				'title'         => get_the_title( $attachment ),
				'alt'           => get_post_meta( $image_id, '_wp_attachment_image_alt', true ),
			);
		}

		$context = ! empty( $request['context'] ) ? $request['context'] : 'view';
		$data    = $this->add_additional_fields_to_object( $data, $request );
		$data    = $this->filter_response_by_context( $data, $context );

		$response = rest_ensure_response( $data );

		$response->add_links( $this->prepare_links( $item, $request ) );

		/**
		 * Filter a term item returned from the API.
		 *
		 * Allows modification of the term data right before it is returned.
		 *
		 * @param WP_REST_Response  $response  The response object.
		 * @param object            $item      The original term object.
		 * @param WP_REST_Request   $request   Request used to generate the response.
		 */
		return apply_filters( "woocommerce_rest_prepare_{$this->taxonomy}", $response, $item, $request );
	}

	/**
	 * Update term meta fields.
	 *
	 * @param WP_Term         $term    Term object.
	 * @param WP_REST_Request $request Request instance.
	 * @return bool|WP_Error
	 */
	protected function update_term_meta_fields( $term, $request ) {
		$id = (int) $term->term_id;

		if ( $request->get_param( 'id_odoo' ) ) {
			update_term_meta( $term->term_id, 'id_odoo', $request->get_param( 'id_odoo' ) );
		}
		if ( $request->get_param( 'cat_header' ) || $request->get_param( 'cat_footer' ) ) {
			$meta_flat = get_term_meta( $term->term_id, 'cat_meta' );
			if ( $request->get_param( 'cat_header' ) ) {
				$meta_flat['cat_header'] = $request->get_param( 'cat_header' );
			}
			if ( $request->get_param( 'cat_footer' ) ) {
				$meta_flat['cat_footer'] = $request->get_param( 'cat_footer' );
			}
			update_term_meta( $term->term_id, 'cat_meta', $meta_flat );
		}

		if ( isset( $request['display'] ) ) {
			update_term_meta( $id, 'display_type', 'default' === $request['display'] ? '' : $request['display'] );
		}

		if ( isset( $request['menu_order'] ) ) {
			update_term_meta( $id, 'order', $request['menu_order'] );
		}

		if ( isset( $request['image'] ) ) {
			if ( empty( $request['image']['id'] ) && ! empty( $request['image']['src'] ) ) {
				$upload = wc_rest_upload_image_from_url( esc_url_raw( $request['image']['src'] ) );

				if ( is_wp_error( $upload ) ) {
					return $upload;
				}

				$image_id = wc_rest_set_uploaded_image_as_attachment( $upload );
			} else {
				$image_id = isset( $request['image']['id'] ) ? absint( $request['image']['id'] ) : 0;
			}

			// Check if image_id is a valid image attachment before updating the term meta.
			if ( $image_id && wp_attachment_is_image( $image_id ) ) {
				update_term_meta( $id, 'thumbnail_id', $image_id );

				// Set the image alt.
				if ( ! empty( $request['image']['alt'] ) ) {
					update_post_meta( $image_id, '_wp_attachment_image_alt', wc_clean( $request['image']['alt'] ) );
				}

				// Set the image title.
				if ( ! empty( $request['image']['title'] ) ) {
					wp_update_post(
						array(
							'ID'         => $image_id,
							'post_title' => wc_clean( $request['image']['title'] ),
						)
					);
				}
			} else {
				delete_term_meta( $id, 'thumbnail_id' );
			}
		}

		return true;
	}

	/**
	 * Get the Category schema, conforming to JSON Schema.
	 *
	 * @return array
	 */
	public function get_item_schema() {
		$schema = array(
			'$schema'    => 'http://json-schema.org/draft-04/schema#',
			'title'      => $this->taxonomy,
			'type'       => 'object',
			'properties' => array(
				'id' => array(
					'description' => __( 'Unique identifier for the resource.', 'woocommerce' ),
					'type'        => 'integer',
					'context'     => array( 'view', 'edit' ),
					'readonly'    => true,
				),
				'name' => array(
					'description' => __( 'Category name.', 'woocommerce' ),
					'type'        => 'string',
					'context'     => array( 'view', 'edit' ),
					'arg_options' => array(
						'sanitize_callback' => 'sanitize_text_field',
					),
				),
				'slug' => array(
					'description' => __( 'An alphanumeric identifier for the resource unique to its type.', 'woocommerce' ),
					'type'        => 'string',
					'context'     => array( 'view', 'edit' ),
					'arg_options' => array(
						'sanitize_callback' => 'sanitize_title',
					),
				),
				'parent' => array(
					'description' => __( 'The ID for the parent of the resource.', 'woocommerce' ),
					'type'        => 'integer',
					'context'     => array( 'view', 'edit' ),
				),
				'description' => array(
					'description' => __( 'HTML description of the resource.', 'woocommerce' ),
					'type'        => 'string',
					'context'     => array( 'view', 'edit' ),
					'arg_options' => array(
						'sanitize_callback' => 'wp_filter_post_kses',
					),
				),
				'display' => array(
					'description' => __( 'Category archive display type.', 'woocommerce' ),
					'type'        => 'string',
					'default'     => 'default',
					'enum'        => array( 'default', 'products', 'subcategories', 'both' ),
					'context'     => array( 'view', 'edit' ),
				),
				'image' => array(
					'description' => __( 'Image data.', 'woocommerce' ),
					'type'        => 'object',
					'context'     => array( 'view', 'edit' ),
					'properties'  => array(
						'id' => array(
							'description' => __( 'Image ID.', 'woocommerce' ),
							'type'        => 'integer',
							'context'     => array( 'view', 'edit' ),
						),
						'date_created' => array(
							'description' => __( "The date the image was created, in the site's timezone.", 'woocommerce' ),
							'type'        => 'date-time',
							'context'     => array( 'view', 'edit' ),
							'readonly'    => true,
						),
						'date_modified' => array(
							'description' => __( "The date the image was last modified, in the site's timezone.", 'woocommerce' ),
							'type'        => 'date-time',
							'context'     => array( 'view', 'edit' ),
							'readonly'    => true,
						),
						'src' => array(
							'description' => __( 'Image URL.', 'woocommerce' ),
							'type'        => 'string',
							'format'      => 'uri',
							'context'     => array( 'view', 'edit' ),
						),
						'title' => array(
							'description' => __( 'Image name.', 'woocommerce' ),
							'type'        => 'string',
							'context'     => array( 'view', 'edit' ),
						),
						'alt' => array(
							'description' => __( 'Image alternative text.', 'woocommerce' ),
							'type'        => 'string',
							'context'     => array( 'view', 'edit' ),
						),
					),
				),
				'menu_order' => array(
					'description' => __( 'Menu order, used to custom sort the resource.', 'woocommerce' ),
					'type'        => 'integer',
					'context'     => array( 'view', 'edit' ),
				),
				'count' => array(
					'description' => __( 'Number of published products for the resource.', 'woocommerce' ),
					'type'        => 'integer',
					'context'     => array( 'view', 'edit' ),
					'readonly'    => true,
				),
			),
		);

		return $this->add_additional_fields_schema( $schema );
	}

}
