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

class HPCtrl
{
    private $mysqli;

    public function __construct($mysqli) 
    {
        $this->mysqli = $mysqli;
    }
    
    public function set($userid,$config)
    {
        $userid = (int) $userid;
        $config = json_encode($config);
        $config = preg_replace('/[^\w\s\-.",:#&{}\[\]]/','',$config);
        
        if (!$result = $this->mysqli->query("SELECT config FROM hpctrl WHERE `userid`='$userid'")) {
            return false;
        }
        if ($result->num_rows) {
            $stmt = $this->mysqli->prepare("UPDATE hpctrl SET `config`=? WHERE `userid`=?");
            $stmt->bind_param("si", $config, $userid);
            if (!$stmt->execute()) return false;
        } else {
            $stmt = $this->mysqli->prepare("INSERT INTO hpctrl ( userid, config ) VALUES (?,?)");
            $stmt->bind_param("is", $userid, $config);
            if (!$stmt->execute()) return false;
        }
        return true;
    }
    
    public function get($userid)
    {
        $userid = (int) $userid;
        if (!$result = $this->mysqli->query("SELECT config FROM hpctrl WHERE `userid`='$userid'")) {
            return false;
        }
        if ($result->num_rows) {
            $row = $result->fetch_array();
            $config = json_decode($row['config']);
            return $config;
        }
        return false;
    }
}
