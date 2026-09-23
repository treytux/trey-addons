#!/bin/bash
echo "Entrypoint base"
sed -i '$ d' /usr/local/bin/docker-entrypoint.sh
/usr/local/bin/docker-entrypoint.sh apache2-foreground
/usr/local/bin/wait-for db:3306 -- echo "MariaDB initializated"
echo "Install woocommerce"
/usr/local/bin/wp --allow-root --path=/var/www/html core install --url=http://localhost:8080 --title=woo --admin_user=admin --admin_email=info@trey.es --admin_password=admin
/usr/local/bin/wp --allow-root --path=/var/www/html plugin activate woocommerce
/usr/local/bin/wp --allow-root --path=/var/www/html plugin activate cl-woodoo-sync
/usr/local/bin/wp --allow-root --path=/var/www/html rewrite structure '/%postname%/'
echo "Install mu-plugin for SSL simulation"
mkdir -p /var/www/html/wp-content/mu-plugins
cp /var/www/html/force-ssl-for-wc-api.php /var/www/html/wp-content/mu-plugins/
echo "Create API keys"
ADMIN_USER_ID=$(/usr/local/bin/wp --allow-root --path=/var/www/html user get admin --field=ID 2>/dev/null || echo 1)

# Ensure admin has the administrator role (Woo permissions are derived from WP caps)
/usr/local/bin/wp --allow-root --path=/var/www/html user set-role admin administrator || true

# Clean any previous WooCommerce API key
/usr/local/bin/wp --allow-root --path=/var/www/html db query "DELETE FROM wp_woocommerce_api_keys WHERE key_id=1 OR consumer_key='a934bb2ebab77dde29925b36ae98bb512666ab9989c62a24f24339bb324902d6';"

# La consumer_key que WooCommerce almacena en BD debe ser el HMAC-SHA256 de la
# clave raw usando 'wc-api' como secreto: hash_hmac('sha256', raw_key, 'wc-api')
# La clave raw que usan los tests es: a934bb2ebab77dde29925b36ae98bb512666ab9989c62a24f24339bb324902d6
# Su hash HMAC-SHA256 con clave 'wc-api' -> 30cfa2a598ff0944febf4211b062f3df011c6b6effb549e93e015232e274176f
INSERT_KEY='30cfa2a598ff0944febf4211b062f3df011c6b6effb549e93e015232e274176f'
INSERT_SECRET='cs_test123456789012345678901234567890123'

/usr/local/bin/wp --allow-root --path=/var/www/html db query "INSERT INTO wp_woocommerce_api_keys SET key_id=1, user_id=${ADMIN_USER_ID}, description='test', permissions='read_write', consumer_key='${INSERT_KEY}', consumer_secret='${INSERT_SECRET}', nonces=NULL, truncated_key='est1234';"

# Aseguramos que las opciones de WooCommerce existen (REPLACE crea o actualiza)
# Usamos REPLACE en lugar de UPDATE porque el option_name puede no existir
/usr/local/bin/wp --allow-root --path=/var/www/html db query "REPLACE INTO wp_options (option_name, option_value, autoload) VALUES ('woocommerce_api_enabled', 'yes', 'yes');"
/usr/local/bin/wp --allow-root --path=/var/www/html db query "UPDATE wp_options SET option_value='0' WHERE option_name='uploads_use_yearmonth_folders';"
chown -R www-data:www-data /var/www/html
exec apache2-foreground
