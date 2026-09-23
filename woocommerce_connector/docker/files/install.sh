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
/usr/local/bin/wp --allow-root --path=/var/www/html db query "INSERT INTO wp_woocommerce_api_keys SET key_id=1, user_id=1, description='test', permissions='read_write', consumer_key='92470e58fc0bfbe3b5ffb258f558261e03a20da87d3028c5bf26a22223f94ce8',  consumer_secret='cs_e8bdd92d641b3ff8ee98b250d30ad138a5cc1ff0', nonces='a:3:{i:1627391883;s:40:\"c4e6710317389fcd4f6dfe61d4a1f5ca0eea0074\";i:1627391884;s:40:\"115f5776577f797c6f4262f6b015ed1a67c08d2a\";i:1627391885;s:40:\"c148286bba555b8696b249891d5cb5d49030b4de\";}', truncated_key='d645d44';"
/usr/local/bin/wp --allow-root --path=/var/www/html db query "UPDATE wp_options SET option_value='yes' WHERE option_name='woocommerce_api_enabled';"
/usr/local/bin/wp --allow-root --path=/var/www/html db query "UPDATE wp_options SET option_value='0' WHERE option_name='uploads_use_yearmonth_folders';"
chown -R www-data:www-data /var/www/html
exec apache2-foreground
