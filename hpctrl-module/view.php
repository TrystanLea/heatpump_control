<?php global $path; $v=3; ?>
<script src="<?php echo $path; ?>Lib/vue.min.js"></script>
<link href="<?php echo $path; ?>Modules/hpctrl/style.css?v=<?php echo $v; ?>" rel="stylesheet">
    
<div id="app" style="max-width:500px">

  <h2>Heatpump Control</h2>
  <div class="saved hide">Saved</div>

  <h3>Space Heating</h3>
  <table class="table">
    <tr><th>Hour</th><th>Set point</th><th>FlowT</th><th>Mode</th><th><button class="btn" @click="add_space"><i class="icon-plus"></i></button></th></tr>
    <tr v-for="(item,index) in config.heating">
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

<h3>Log</h3>
<pre style="max-width:1000px"><div id="log"></div></pre>


<script>
var config = {};

$.ajax({ url: path+"hpctrl/get-config", dataType: 'json', success: function(result){

    if (!result || result==null) {
        config = {
            "heating": [
                {"h":0,"set_point":18.5,"flowT":31.0,"mode":"min"},
                {"h":6,"set_point":20.0,"flowT":34.0,"mode":"min"},
                {"h":15,"set_point":21.0,"flowT":36.0,"mode":"max"},
                {"h":16,"set_point":20.4,"flowT":31.0,"mode":"min"},
                {"h":17,"set_point":20.2,"flowT":31.0,"mode":"min"},
                {"h":18,"set_point":20.0,"flowT":31.0,"mode":"min"},
                {"h":19,"set_point":21.0,"flowT":34.0,"mode":"min"},
                {"h":21,"set_point":20.0,"flowT":31.0,"mode":"min"}
            ],
            "dhw": [
                {"start":"0700","T":40.0,"flowT":'auto', "mode":"min"},
                {"start":"1400","T":40.0,"flowT":'auto', "mode":"min"}
            ]
        }
    } else {
        config = result
    }
    
    var app = new Vue({
        el: '#app',
        data: {
            config:config
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
                if (config["heating"].length>0) {       
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
            }
        }
    });
}});

function update_log(){
    $.ajax({
        url: path+"hpctrl/log",
        dataType: 'text', async: true,
        success: function(data) {
            $("#log").html(data+"\n\n");
        }
    });
}

update_log();
setInterval(update_log,5000);

</script>
