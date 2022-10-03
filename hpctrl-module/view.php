<?php global $path; $v=3; ?>
<script src="<?php echo $path; ?>Lib/vue.min.js"></script>
<link href="<?php echo $path; ?>Modules/hpctrl/style.css?v=<?php echo $v; ?>" rel="stylesheet">
    
<style>
#live td {
  text-align:center;
  width:25%;
}

.set_point {
  font-size:48px;
  padding:20px;
  display:inline-block
}

.room_temperature {
  margin-top:5px;
  margin-bottom:20px;
}
.set_point_ctrl {
  display:inline-block;
  padding:10px;
  font-size:48px;
}

</style>
    
<div id="app" style="max-width:500px">


  <div class="saved hide">Saved</div>
  
  <div style="text-align:center">
    <h2>Heatpump Control</h2>
    <p>SET POINT</p>
    <div class="set_point_ctrl"><button @click="dec_set_point">-</button></div>
    <div class="set_point">{{ config.heating[active_period].set_point }}</div>
    <div class="set_point_ctrl"><button @click="inc_set_point">+</button></div>
    <div class="room_temperature">Temperature: {{ room_temperature | toFixed(1) }}&#8451;</div>
  </div>
  
  <table id="live" class="table">
    <tr>
      <td><b>Flow</b><br>{{ flow_temperature | toFixed(1) }}&#8451;</td>
      <td><b>Outside</b><br>{{ outside_temperature | toFixed(1) }}&#8451;</td>
      <td><b>Elec</b><br>{{ heatpump_elec | toFixed(0) }}W</td>
      <td><b>Heat</b><br>{{ heatpump_heat | toFixed(0) }}W</td>
    </tr>
  </table>
  
  <div style="float:right">{{ time }}</div>
   
  <h3>Space Heating</h3>
  <table class="table">
    <tr><th>Hour</th><th>Set point</th><th>FlowT</th><th>Mode</th><th><button class="btn" @click="add_space"><i class="icon-plus"></i></button></th></tr>
    <tr v-for="(item,index) in config.heating" v-bind:class="{ warning: index==active_period }">
      <td><input type="text" v-model.number="item.h" @change="save"/></td>
      <td><input type="text" v-model.number="item.set_point" @change="save"/></td>
      <td><input type="text" v-model.number="item.flowT" @change="save"/></td>
      <td><select v-model="item.mode" @change="save">
        <option>min</option>
        <option>max</option>
      </select></td>
      <td><button class="btn"  @click="delete_space(index)"><i class="icon-trash"></i></button></td> 
    </tr>
  </table>

  
  <h3>DHW</h3>
  <table class="table">
    <tr><th>Start</th><th>Target</th><th>FlowT</th><th></th><th><button class="btn" @click="add_dhw"><i class="icon-plus"></i></button></th></tr>
    <tr v-for="(item,index) in config.dhw">
      <td><input type="text" v-model="item.start" @change="save"/></td>
      <td><input type="text" v-model.number="item.T" @change="save"/></td>
      <td><input type="text" v-if="item.mode=='max'" v-model.number="item.flowT" @change="save"/><span v-else>AUTO</span></td>
      <td><select v-model="item.mode" @change="save">
        <option>min</option>
        <option>max</option>
      </select></td>
      <td><button class="btn" @click="delete_dhw(index)"><i class="icon-trash"></i></button></td> 
    </tr>
  </table>
</div>


<script>
var config = {};
var app = {};
var save_inst = false;

$.ajax({ url: path+"hpctrl/get-config", dataType: 'json', success: function(result){

    if (!result || result==null) {
        config = {
            "heating": [
                {"h":0,"set_point":5,"flowT":20.0,"mode":"min"}
            ],
            "dhw": [
                {"start":"0200","T":42.0,"flowT":'auto', "mode":"min"},
                {"start":"1400","T":42.0,"flowT":'auto', "mode":"min"}
            ]
        }
    } else {
        config = result
    }
    
    app = new Vue({
        el: '#app',
        data: {
            config:config,
            
            time: '',
            current_set_point: 18.0,
            
            active_period: 0,
            
            room_temperature:'',
            flow_temperature:'',
            outside_temperature:'',
            heatpump_elec:'',
            heatpump_heat:'',
            heatpump_cop:0
        },
        filters: {
           toFixed: function(val,dp) {
               if (!isNaN(val)) {
                   val = val * 1;
                   return val.toFixed(1)
               } else {
                   return val
               }
           }
        },
        methods: {
            save: function() {
                $.ajax({ method: "POST", url: path+"hpctrl/set-config", data:"config="+JSON.stringify(config), dataType: 'json', async: false, success: function(result){
                    if (result.success!=undefined && result.success) {
                        $(".saved").show();
                        setTimeout(function(){
                            $(".saved").hide();
                        },2000);
                    } else {
                        alert("Could not save")
                    }
                }});
            },
            add_space: function() {
                if (config["heating"].length>0) {
                    var last = JSON.parse(JSON.stringify(config["heating"][config["heating"].length-1]))
                    last.h += 1;
                    if (last.h>23) last.h = 23;
                    config["heating"].push(last);       
                } else {
                    config["heating"].push({"h":0,"set_point":20.0,"flowT":32.0,"mode":"max"});
                }
                app.save();
            },
            add_dhw: function() {
                if (config["dhw"].length>0) {       
                    var last = JSON.parse(JSON.stringify(config["dhw"][config["dhw"].length-1]))
                    config["dhw"].push(last);
                } else {
                    config["dhw"].push({"start":"0700","T":40.0,"flowT":"auto","mode":"min"});
                }
                app.save();
            },
            delete_space: function(index) {
                config["heating"].splice(index,1);  
                app.save();
            },
            delete_dhw: function(index) {
                config["dhw"].splice(index,1);
                app.save();
            },
            inc_set_point: function() {
                app.config.heating[app.active_period].set_point += 0.1;
                app.config.heating[app.active_period].set_point = app.config.heating[app.active_period].set_point.toFixed(1)
                app.config.heating[app.active_period].set_point *= 1;
                clearTimeout(save_inst);
                save_inst = setTimeout(function() {app.save()},2000); 
            },
            dec_set_point: function() {
                app.config.heating[app.active_period].set_point -= 0.1;        
                app.config.heating[app.active_period].set_point = app.config.heating[app.active_period].set_point.toFixed(1)
                app.config.heating[app.active_period].set_point *= 1;
                clearTimeout(save_inst);
                save_inst = setTimeout(function() {app.save()},2000); 
            }
        }
    });
    update_log();
}});

function update_log(){
    /*$.ajax({
        url: path+"hpctrl/log",
        dataType: 'text', async: true,
        success: function(data) {
            $("#log").html(data+"\n\n");
        }
    });*/
    
    $.ajax({
        url: path+"feed/fetch.json?ids=165195,165118,165140,165228,165234",
        dataType: 'json', async: true,
        success: function(data) {
            app.room_temperature = data[0]
            app.flow_temperature = data[1]
            app.outside_temperature = data[2]
            app.heatpump_elec = data[3]
            app.heatpump_heat = data[4]
            app.heatpump_cop = data[4]/data[3]
        }
    });
    
    var d = new Date();
    h = d.getHours();
    m = d.getMinutes();
    app.time = String(h).padStart(2,'0')+":"+String(m).padStart(2,'0')
    
    var h = h+(m/60)
    for (var z in app.config.heating) {
        if (h>app.config.heating[z].h) {
            app.current_set_point = app.config.heating[z].set_point
            
            app.active_period = z
            
        }
    }
    
}
setInterval(update_log,10000);

</script>
