<?php
  /*
   All Emoncms code is released under the GNU Affero General Public License.
   See COPYRIGHT.txt and LICENSE.txt.

    ---------------------------------------------------------------------
    Emoncms - open source energy visualisation
    Part of the OpenEnergyMonitor project:
    http://openenergymonitor.org
  */

// no direct access
defined('EMONCMS_EXEC') or die('Restricted access');

function hpctrl_controller()
{
    global $mysqli, $redis, $session, $route, $settings;

    $result = false;
    
    if ($route->action == '' && $session['write']) {
        return view("Modules/hpctrl/view.php",array());
    }

    if ($route->action == 'get-config' && $session['read']) {
        $route->format = "json";
        return json_decode($redis->get("hpctrl"));
    }

    if ($route->action == 'set-config' && $session['write']) {
        $route->format = "json";
        if (isset($_POST['config'])) {
            $config = json_decode($_POST['config']);
            if ($config) {
                $redis->set("hpctrl",json_encode($config));
                
                $client = new Mosquitto\Client();
                $client->setCredentials($settings['mqtt']['user'],$settings['mqtt']['password']);
                $client->connect($settings['mqtt']['host'], $settings['mqtt']['port'], 5);
                $client->publish("hpctrl/config", json_encode($config),0,true);
            
                return array("success"=>"true");
            }        
        }
    }

    else if ($route->action == 'log') {
        $route->format = "text";
        ob_start();
        if (file_exists("/var/log/emoncms/hpctrl.log")) {
            passthru("tail -30 /var/log/emoncms/hpctrl.log");
        }   
        $result = trim(ob_get_clean());
    }

    return array('content'=>$result);
}
