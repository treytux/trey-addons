<?php
/**
 * Common functions for connect id to id_odoo
 *
 * @package WooDoo
 * @depends WCML
 */

/**
 * Check if product exists by product meta id_odoo.
 *
 * @param  int $id_odoo la id de Odoo.
 * @return array
 */
function check_if_exists_product_odoo( $id_odoo ) {
	global $wpdb;
	$sql     = $wpdb->prepare( 'SELECT pm.post_id FROM ' . $wpdb->postmeta . ' pm WHERE pm.meta_key = "id_odoo" AND pm.meta_value = %s LIMIT 1', $id_odoo );
	$results = $wpdb->get_results( $sql, ARRAY_A ); // phpcs:ignore Standard.Category.SniffName.ErrorCode: unprepared SQL OK.
	return $results[0];
}

/**
 * Check if variation exists by product meta id_odoo.
 *
 * @param  int $id_odoo la id de Odoo.
 * @return array
 */
function check_if_exists_variation_odoo( $id_odoo ) {
	global $wpdb;
	$sql     = $wpdb->prepare( 'SELECT pm.post_id FROM ' . $wpdb->postmeta . ' pm INNER JOIN ' . $wpdb->posts . ' p ON pm.post_id = p.ID AND p.post_type = "product_variation" WHERE pm.meta_key = "id_odoo" AND pm.meta_value = %s LIMIT 1', $id_odoo );
	$results = $wpdb->get_results( $sql, ARRAY_A ); // phpcs:ignore Standard.Category.SniffName.ErrorCode: unprepared SQL OK.
	return $results[0];
}

/**
 * Search product id by product meta id_odoo.
 *
 * @param int $id_odoo la id de Odoo.
 * @return array
 */
function check_if_exists_category_odoo( $id_odoo ) {
	global $wpdb;
	$sql     = $wpdb->prepare( 'SELECT tm.term_id FROM ' . $wpdb->termmeta . ' tm INNER JOIN ' . $wpdb->term_taxonomy . ' tt ON tm.term_id = tt.term_id AND tt.taxonomy = "product_cat" WHERE tm.meta_key = "id_odoo" AND tm.meta_value = %s LIMIT 1', $id_odoo );
	$results = $wpdb->get_results( $sql, ARRAY_A ); // phpcs:ignore Standard.Category.SniffName.ErrorCode: unprepared SQL OK.
	return $results[0];
}

/**
 * Search product id by product meta id_odoo.
 *
 * @param int $id_odoo la id de Odoo.
 * @return array
 */
function check_if_exists_tag_odoo( $id_odoo ) {
	global $wpdb;
	$sql     = $wpdb->prepare( 'SELECT tm.term_id FROM ' . $wpdb->termmeta . ' tm INNER JOIN ' . $wpdb->term_taxonomy . ' tt ON tm.term_id = tt.term_id AND tt.taxonomy = "product_tag" WHERE tm.meta_key = "id_odoo" AND tm.meta_value = %s LIMIT 1', $id_odoo );
	$results = $wpdb->get_results( $sql, ARRAY_A ); // phpcs:ignore Standard.Category.SniffName.ErrorCode: unprepared SQL OK.
	return $results[0];
}

/**
 * Search marca id by marca meta id_odoo.
 *
 * @param int $id_odoo la id de Odoo.
 * @return array
 */
function check_if_exists_marca_odoo( $id_odoo ) {
	global $wpdb;
	$sql     = $wpdb->prepare( 'SELECT tm.term_id FROM ' . $wpdb->termmeta . ' tm INNER JOIN ' . $wpdb->term_taxonomy . ' tt ON tm.term_id = tt.term_id AND tt.taxonomy = "marcas" WHERE tm.meta_key = "id_odoo" AND tm.meta_value = %s LIMIT 1', $id_odoo );
	$results = $wpdb->get_results( $sql, ARRAY_A ); // phpcs:ignore Standard.Category.SniffName.ErrorCode: unprepared SQL OK.
	return $results[0];
}

/**
 * Search marca id by marca meta id_odoo.
 *
 * @param int $slug la id de Odoo.
 * @return array
 */
function check_if_exists_attribute_odoo( $slug ) {
	global $wpdb;
	$sql     = $wpdb->prepare( 'SELECT wat.attribute_name FROM ' . $wpdb->prefix . 'woocommerce_attribute_taxonomies wat WHERE wat.attribute_name = %s LIMIT 1', $slug );
	$results = $wpdb->get_results( $sql, ARRAY_A ); // phpcs:ignore Standard.Category.SniffName.ErrorCode: unprepared SQL OK.
	return $results[0];
}

/**
 * Search an attribute by his slug
 *
 * @param [type] $slug
 * @return void
 */
function get_attribute_id_by_slug( $slug ) {
	global $wpdb;
	$sql     = $wpdb->prepare( 'SELECT wat.attribute_id FROM ' . $wpdb->prefix . 'woocommerce_attribute_taxonomies wat WHERE wat.attribute_name = %s LIMIT 1', $slug );
	$results = $wpdb->get_results( $sql, ARRAY_A ); // phpcs:ignore Standard.Category.SniffName.ErrorCode: unprepared SQL OK.
	return $results[0];
}

/**
 * Search product id by product meta id_odoo.
 *
 * @param int    $id la id de Odoo.
 * @param string $lang idioma en el que se busca la categoría.
 * @return array
 */
function get_product_id_by_idodoo( $id, $lang ) {
	global $wpdb;
	$sql = $wpdb->prepare( 'SELECT pm.post_id FROM ' . $wpdb->postmeta . ' pm INNER JOIN ' . $wpdb->prefix . 'icl_translations tml ON pm.post_id = tml.element_id AND tml.language_code = "' . $lang . '" WHERE pm.meta_key = "id_odoo" AND pm.meta_value = %s', $id );

	$results = $wpdb->get_results( $sql, ARRAY_A ); // phpcs:ignore Standard.Category.SniffName.ErrorCode: unprepared SQL OK.

	return $results[0];
}

/**
 * Search category id by meta id_odoo.
 *
 * @param int    $id la id de Odoo.
 * @param string $lang idioma en el que se busca la categoría.
 * @return array
 */
function get_category_id_by_idodoo( $id, $lang ) {
	global $wpdb;
	$sql     = $wpdb->prepare( 'SELECT tm.term_id FROM ' . $wpdb->termmeta . ' tm INNER JOIN ' . $wpdb->prefix . 'icl_translations tml ON tm.term_id = tml.element_id AND tml.language_code = "' . $lang . '" WHERE tm.meta_key = "id_odoo" AND tm.meta_value = %s', $id );

	$results = $wpdb->get_results( $sql, ARRAY_A ); // phpcs:ignore Standard.Category.SniffName.ErrorCode: unprepared SQL OK.

	return $results[0];
}

/**
 * Search marca id by meta id_odoo.
 *
 * @param int    $id la id de Odoo.
 * @return array
 */
function get_marca_id_by_idodoo( $id ) {
	global $wpdb;
	$sql     = $wpdb->prepare( 'SELECT tm.term_id FROM ' . $wpdb->termmeta . ' tm INNER JOIN ' . $wpdb->term_taxonomy . ' tt ON tm.term_id = tt.term_id AND tt.taxonomy = "marcas" WHERE tm.meta_key = "id_odoo" AND tm.meta_value = %s', $id );

	$results = $wpdb->get_results( $sql, ARRAY_A ); // phpcs:ignore Standard.Category.SniffName.ErrorCode: unprepared SQL OK.

	return $results[0];
}

/**
 * Search comercial id by meta id_odoo.
 *
 * @param int $id_odoo la id de Odoo.
 * @return int
 */
function get_comercial_id_by_idodoo( $id_odoo ) {
	$query = new WP_Query(
		array(
			'post_type'      => 'comerciales',
			'meta_key'       => 'id_odoo',
			'meta_value'     => $id_odoo,
			'posts_per_page' => 1,
		)
	);
	if ( $query->found_posts > 0 ) {
		$id_wp = $query->posts[0]->ID;
	} else {
		$id_wp = false;
	}
	return $id_wp;
}

/**
 * Search user id by meta id_odoo.
 *
 * @param int $id_odoo la id de Odoo.
 * @return int
 */
function get_user_id_by_idodoo( $id_odoo ) {
	$users = get_users(
		array(
			'meta_key'   => 'id_odoo',
			'meta_value' => $id_odoo,
			'number'     => 1,
		)
	);
	return ! empty( $users[0] ) ? $users[0]->id : false;
}
