<?php
class OdooApi {
    public $url;
    public $session_id;

    function __construct($url) {
        $this->url = $url;
    }

    function request($endpoint, $params) {
        $ch = curl_init($this->url . $endpoint);
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($params));
        curl_setopt($ch, CURLOPT_HTTPHEADER, array(
            'Content-Type: application/json',
            'Accept: application/json',
            'X-Openerp-Session-Id:'. $this->session_id,
        ));
        curl_setopt($ch, CURLOPT_VERBOSE, true);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HEADER, 1);
        $response = curl_exec($ch);
        curl_close($ch);

        $lines = explode("\n", $response);
        $headers = array();
        $body = "";
        foreach($lines as $num => $line){
            $l = str_replace("\r", "", $line);
            if(trim($l) == ""){
                $headers = array_slice($lines, 0, $num);
                $body = $lines[$num + 1];
                break;
            }
        }
        preg_match_all('/^Set-Cookie:\s*([^;]*)/mi', $response, $matches);        // get cookie
        $cookies = array();
        foreach($matches[1] as $item) {
            parse_str($item, $cookie);
            $cookies = array_merge($cookies, $cookie);
        }
        if (array_key_exists('session_id', $cookies)){
            $this->session_id = $cookies['session_id'];
        }
        $result = json_decode($body, true);
        if (array_key_exists('error', $result)) {
            $error = $result['error'];
            echo '(' . $error['code'] . ') ' . $error['message'] . '\n';
            echo $error['data']['debug'] . '\n';
            return $result;
        }
        return $result;
    }

    function login($db, $login, $password){
        $response = $this->request(
            '/web/session/authenticate',
            array(
                'params' => array(
                    'db' => $db,
                    'login' => $login,
                    'password' => $password,
                ),
            )
        );
        var_dump($response['result']['uid']);
        if (
            array_key_exists('result', $response)
            && array_key_exists('uid', $response['result'])) {
                return true;
        }
        return false;
    }
}

$oo = new OdooApi('http://localhost:8069');
if (!$oo->login('bd_test', 'admin', 'admin')) {
    print('Login error.');
    exit(-1);
}
$oo->request('/sale_order/import',
    array(
        'name' => 'SO335',
        'partner' => [
            'name' => 'Customer',
            'street' => 'Customer Street',
            'email' => 'new@partner.com',
        ],
        'partner_shipping' => [
            'name' => 'Shipping',
            'street' => 'Shipping Street',
            'email' => 'new@shipping.com',
        ],
        'order_line'=> array(
                [
                    'default_code' => 'TEST-01',
                    'product_uom_qty' => 1,
                    'price_unit_taxed' => 95.59,
                    'price_unit_untaxed' => 79,
                ],
                [
                    'default_code' => 'TEST-02',
                    'product_uom_qty' => 2,
                    'price_unit_taxed' => 30.25,
                    'price_unit_untaxed' => 25,
                ],
        ),
        'note' => 'Description',
        'state' => 'confirmed',
        'warehouse_id' => 1,
        'journal_name' => 'Facturas de cliente',
        'payment_method_name' => 'Electrónico',
        'invoice_date' => '2021-09-07',
    )
);
?>
