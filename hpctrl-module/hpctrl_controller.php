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
    global $mysqli, $session, $route, $settings;

    $result = false;
    
    require_once "/opt/emoncms/modules/hpctrl/ui_settings.php";
    
    if (!$session['write']) return false;
    if (!in_array($session['userid'],$hpctrl_users)) return false;
    
    if ($route->action == '' && $session['write']) {
        return view("Modules/hpctrl/view.php",array('dhw_enable'=>$dhw_enable));
    }

    if ($route->action == 'get-config' && $session['read']) {
        $route->format = "json";
        require "Modules/hpctrl/hpctrl_model.php";
        $hpctrl = new HPCtrl($mysqli);
        return $hpctrl->get($session['userid']);
    }

    if ($route->action == 'set-config' && $session['write']) {
        $route->format = "json";
        if (isset($_POST['config'])) {
            $config = json_decode($_POST['config']);
            if ($config) {                
                require "Modules/hpctrl/hpctrl_model.php";
                $hpctrl = new HPCtrl($mysqli);
                $hpctrl->set($session['userid'],$config);
                
                if ($mqtt_enable) {
                    $client = new Mosquitto\Client();
                    $client->setCredentials($settings['mqtt']['user'],$settings['mqtt']['password']);
                    $client->connect($settings['mqtt']['host'], $settings['mqtt']['port'], 5);
                    $client->publish("hpctrl/config", json_encode($config),0,true);
                }
                return array("success"=>"true");
            }        
        }
    }

    return array('content'=>$result);
}
