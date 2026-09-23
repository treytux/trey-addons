FROM wordpress:latest

ENV WOOCOMMERCE_VERSION 2.6.1
ENV WOOCOMMERCE_UPSTREAM_VERSION 2.6.1

RUN apt-get update
RUN apt-get install -y --no-install-recommends git ssh unzip wget less mariadb-client netcat-traditional

RUN wget https://github.com/woocommerce/woocommerce/releases/download/nightly/woocommerce-trunk-nightly.zip -O /tmp/temp.zip \
    && cd /usr/src/wordpress/wp-content/plugins \
    && unzip /tmp/temp.zip \
    && rm /tmp/temp.zip

RUN wget https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar -O /usr/local/bin/wp \
    && chmod +x /usr/local/bin/wp

RUN wget https://raw.githubusercontent.com/eficode/wait-for/v2.1.2/wait-for -O /usr/local/bin/wait-for \
    && chmod +x /usr/local/bin/wait-for

COPY ./files/id_rsa_container.pub /root/.ssh/id_rsa.pub
COPY ./files/id_rsa_container /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/*

COPY ./files/WoOdoo-sync-master.tar.gz /usr/src/wordpress/wp-content/plugins/
RUN tar xvzf /usr/src/wordpress/wp-content/plugins/WoOdoo-sync-master.tar.gz -C /usr/src/wordpress/wp-content/plugins

COPY ./files/install.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/install.sh
ENTRYPOINT ["/usr/local/bin/install.sh"]
