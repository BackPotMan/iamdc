
var casetype_grid = "#casetype-table";
var casetype_pager = "#casetype-pager";

jQuery(function($) {

    // table
    jQuery(casetype_grid).jqGrid({
        //direction: "rtl",
        //data: 'json',
        //mtype: 'POST',
        url: '/case/type?type=load',
        datatype: "json",
        height: 'auto',
        colNames:['ID','工单类型名称','审核流程','处理流程','状态','创建时间',' '],
        colModel:[
            {name:'id',index:'id', width:70, sorttype:"int", editable: false},
            {name:'name',index:'name', width:150,editable: false},
            {name:'audit_model',index:'audit_flow', width:150,editable: false},
            {name:'exec_model',index:'exec_flow', width:150,editable: false},
            {name:'status',index:'status', width:70,editable: false},
            {name:'ctime',index:'ctime', width:110,editable: false},
            {name:'myac',index:'', width:100, fixed:true, sortable:false, resize:false}
        ],

        viewrecords : true,
        rowNum:10,
        rowList:[10,20,30],
        pager : casetype_pager,
        altRows: true,
        //toppager: true,

        multiselect: true,
        //multikey: "ctrlKey",
        multiboxonly: true,

        loadComplete : function() {
            var table = this;
            setTimeout(function(){
                styleCheckbox(table);
                updateActionIcons(table);
                updatePagerIcons(table);
                enableTooltips(table);
            }, 0);
        },

        editurl: '/case/type/',//nothing is saved 注意结尾/ , APPEND_SLASH
        caption: "工单类型管理",
        autowidth: true,

        //数据结构格式
        jsonReader: {
            root: "data",
            total: "total",
            page: "page",
            records: "records",
            repeatitems: false,
        },

        // 定义编辑/删除按钮
        gridComplete : function() {
          var ids = jQuery(casetype_grid).jqGrid('getDataIDs');
          for ( var i = 0; i < ids.length; i++) {
            var typeid=$(casetype_grid).jqGrid('getCell',ids[i],1);
            var typename=$(casetype_grid).jqGrid('getCell',ids[i],2);
            be = '<button class="btn btn-primary btn-xs" data-toggle="modal" data-target="#modalCaseTypeOperating" onclick="editCaseType('+typeid+');">编辑</button>  <button class="btn btn-danger btn-xs" data-toggle="modal" data-target="#modalCaseTypeDelete" onclick="delCaseType(\''+typeid+'\',\''+typename+'\');">删除</button>';
            jQuery(casetype_grid).jqGrid('setRowData', ids[i],
                {
                  myac : be
                });
          }
        },
    });

    //navButtons 自定义按钮
    jQuery(casetype_grid).jqGrid('navGrid',casetype_pager,{edit:false,add:false,del:false,search:false,refresh:false}).jqGrid('navButtonAdd',casetype_pager,{
        caption:"",
        buttonicon:'icon-plus-sign purple',
        onClickButton: function(){
                //alert("Adding Row");
                getUsers();
                $('#modalCaseTypeOperating').modal('show');
            },
        position:"first",
        title:'新增',
    }).jqGrid('navButtonAdd',casetype_pager,{
       caption:"",
       buttonicon:'icon-trash red',
       onClickButton: function(){
         //alert("Adding Row");
         var selectedIds = $(casetype_grid).jqGrid("getGridParam", "selarrrow");
         if(selectedIds == ""){
            alert("请先选择行");
            return "" ;
         };

         var ul_list=""
         var id_list=""
         //alert(selectedIds);
         for(cl in selectedIds){

            //alert($(casetype_grid).jqGrid('getCell',selectedIds[cl],1));
            var typeid=$(casetype_grid).jqGrid('getCell',selectedIds[cl],1);
            var typename=$(casetype_grid).jqGrid('getCell',selectedIds[cl],2);

            ul_list = ul_list+'<li class="text-danger"><b> ID: </b>'+typeid+' ; <b>类型名称: </b>'+typename+'</li>'
            if(id_list == ""){
                id_list = typeid
            }else{
                id_list = typeid+","+id_list
            }
         };

         document.getElementById('casetype_id_list').value = id_list ;
         $("#suredellist").html(ul_list)
         $('#modalCaseTypeDelete').modal('show');

       },
       position:"last",
       title:'删除',
    }).jqGrid('navButtonAdd',casetype_pager,{
       caption:"",
       buttonicon:'icon-refresh green',
       onClickButton: function(){
            //alert("refresh Row");
            //$('#modalid').modal('show');
            jQuery(casetype_grid).jqGrid('setGridParam', {}).trigger("reloadGrid");
       },
       position:"last",
       title:'刷新',
    });

    //enable search/filter toolbar
    //jQuery(casetype_grid).jqGrid('filterToolbar',{defaultSearch:true,stringResult:true})

    function style_edit_form(form) {
        //enable datepicker on "sdate" field and switches for "stock" field
        form.find('input[name=sdate]').datepicker({format:'yyyy-mm-dd' , autoclose:true})
            .end().find('input[name=stock]')
                  .addClass('ace ace-switch ace-switch-5').wrap('<label class="inline" />').after('<span class="lbl"></span>');

        //update buttons classes
        var buttons = form.next().find('.EditButton .fm-button');
        buttons.addClass('btn btn-sm').find('[class*="-icon"]').remove();//ui-icon, s-icon
        buttons.eq(0).addClass('btn-primary').prepend('<i class="icon-ok"></i>');
        buttons.eq(1).prepend('<i class="icon-remove"></i>')

        buttons = form.next().find('.navButton a');
        buttons.find('.ui-icon').remove();
        buttons.eq(0).append('<i class="icon-chevron-left"></i>');
        buttons.eq(1).append('<i class="icon-chevron-right"></i>');
    }

    function style_delete_form(form) {
        var buttons = form.next().find('.EditButton .fm-button');
        buttons.addClass('btn btn-sm').find('[class*="-icon"]').remove();//ui-icon, s-icon
        buttons.eq(0).addClass('btn-danger').prepend('<i class="icon-trash"></i>');
        buttons.eq(1).prepend('<i class="icon-remove"></i>')
    }

    function style_search_filters(form) {
        form.find('.delete-rule').val('X');
        form.find('.add-rule').addClass('btn btn-xs btn-primary');
        form.find('.add-group').addClass('btn btn-xs btn-success');
        form.find('.delete-group').addClass('btn btn-xs btn-danger');
    }

    function style_search_form(form) {
        var dialog = form.closest('.ui-jqdialog');
        var buttons = dialog.find('.EditTable')
        buttons.find('.EditButton a[id*="_reset"]').addClass('btn btn-sm btn-info').find('.ui-icon').attr('class', 'icon-retweet');
        buttons.find('.EditButton a[id*="_query"]').addClass('btn btn-sm btn-inverse').find('.ui-icon').attr('class', 'icon-comment-alt');
        buttons.find('.EditButton a[id*="_search"]').addClass('btn btn-sm btn-purple').find('.ui-icon').attr('class', 'icon-search');
    }

    function beforeDeleteCallback(e) {
        var form = $(e[0]);
        if(form.data('styled')) return false;

        form.closest('.ui-jqdialog').find('.ui-jqdialog-titlebar').wrapInner('<div class="widget-header" />')
        style_delete_form(form);

        form.data('styled', true);
    }

    function beforeEditCallback(e) {
        var form = $(e[0]);
        form.closest('.ui-jqdialog').find('.ui-jqdialog-titlebar').wrapInner('<div class="widget-header" />')
        style_edit_form(form);
    }

    //it causes some flicker when reloading or navigating grid
    //it may be possible to have some custom formatter to do this as the grid is being created to prevent this
    //or go back to default browser checkbox styles for the grid
    function styleCheckbox(table) {
        /**
        $(table).find('input:checkbox').addClass('ace')
        .wrap('<label />')
        .after('<span class="lbl align-top" />')


        $('.ui-jqgrid-labels th[id*="_cb"]:first-child')
        .find('input.cbox[type=checkbox]').addClass('ace')
        .wrap('<label />').after('<span class="lbl align-top" />');
        */
    }

    //unlike navButtons icons, action icons in rows seem to be hard-coded
    //you can change them like this in here if you want
    function updateActionIcons(table) {
        /**
        var replacement =
        {
            'ui-icon-pencil' : 'icon-pencil blue',
            'ui-icon-trash' : 'icon-trash red',
            'ui-icon-disk' : 'icon-ok green',
            'ui-icon-cancel' : 'icon-remove red'
        };
        $(table).find('.ui-pg-div span.ui-icon').each(function(){
            var icon = $(this);
            var $class = $.trim(icon.attr('class').replace('ui-icon', ''));
            if($class in replacement) icon.attr('class', 'ui-icon '+replacement[$class]);
        })
        */
    }

    //replace icons with FontAwesome icons like above
    function updatePagerIcons(table) {
        var replacement =
        {
            'ui-icon-seek-first' : 'icon-double-angle-left bigger-140',
            'ui-icon-seek-prev' : 'icon-angle-left bigger-140',
            'ui-icon-seek-next' : 'icon-angle-right bigger-140',
            'ui-icon-seek-end' : 'icon-double-angle-right bigger-140'
        };
        $('.ui-pg-table:not(.navtable) > tbody > tr > .ui-pg-button > .ui-icon').each(function(){
            var icon = $(this);
            var $class = $.trim(icon.attr('class').replace('ui-icon', ''));

            if($class in replacement) icon.attr('class', 'ui-icon '+replacement[$class]);
        })
    }

    function enableTooltips(table) {
        $('.navtable .ui-pg-button').tooltip({container:'body'});
        $(table).find('.ui-pg-div').tooltip({container:'body'});
    }

});


// 获取用户名单,设置(工单处理人)下拉选择框
function getUsers(){
    $.ajax({
        url: '/users/user/',
        type: "POST",
        dataType: "json",
        data:{'oper':"getusers"},
        error: function () {
            alert("getUsers error");
        },
        success: function (data) {

            $("#casetype_executor").append('<option value="0">--选择工单处理人--</option>');

            for( key_num in data ){
                $("#casetype_executor").append('<option value="' + data[key_num]['id'] + '">' + data[key_num]['cnname'] + '(' + data[key_num]['name']  + ')</option>');
            };

        }
    });
}

// 添加(审核人)下拉选择框样式
function addCheckLeaderCSS(obj){
    if($(obj).prev().is("select")){
        var preval = $(obj).prev().val();
    }else if($(obj).prev().is("span")){
        var preval = $(obj).prev().find(".checkleader").val();
    }
    var hasboss = false;
    $(".checkleader").each(function(){
        if($(this).val() == "-1"){
            hasboss = true;
        }
    })
    if(hasboss == true){  //前面是默认上级,那么后面只能是指定人选了
        var len = $(".checkleader").length;
        $(obj).before('<span class="morecheckleader"><span class="glyphicon glyphicon-arrow-right"></span><select class="checkleader" id="checkleader_'+len+'" onchange="changeCheckLeader(this);" style="width:100px" num="0"><option value = "-2">指定人选</option></select></span>');
        getCheckLeader($("#checkleader_"+len));
    }else{
        $(obj).before('<span class="morecheckleader"><span class="glyphicon glyphicon-arrow-right"></span><select class="checkleader" onchange="changeCheckLeader(this);" style="width: 100px"> <option value="-1">默认上级</option><option value = "-2">指定人选</option></select></span>')
    }
    if($(obj).next().is("a")) {
    }else{
        $(obj).after('<a class="btn btn-xs btn-primary" onclick="delCheckLeaderCSS(this)" style="margin-left: 5px" id="delcheckleader">删除一级</a>')
    }
}

// 删除(审核人)下拉选择框样式
function delCheckLeaderCSS(obj){
    if($(obj).prev().prev().is("span") && $(obj).prev().prev().prev().is("select")){
        $(obj).prev().prev().remove();
        $(obj).remove();
    }else if($(obj).prev().prev().is("span") && $(obj).prev().prev().prev().is("span")){
        $(obj).prev().prev().remove();
    }
    if($(obj).prev().prev().hasClass("firstcheckleader")){
        $(obj).remove();
    }
}

// 获取审核人名单,设置(指定审核人)下拉选择框
function getCheckLeader(obj){
    $.ajax({
        url: '/users/user/',
        type: "POST",
        dataType: "json",
        data:{'oper':"getusers"},
        error: function () {
            obj.parent().html((obj.parent().hasClass('firstcheckleader') ? '':'<span class="glyphicon glyphicon-arrow-right"></span>') +'<select class="checkleader" style="width:140px" ><option value="0">--选择指定审核人--</option></select>');
        },
        success: function (data) {

            var oplist = new Array();
            for( key_num in data ){
                oplist.push('<option value="' + data[key_num]['id'] + '">' + data[key_num]['cnname'] + '(' + data[key_num]['name']  + ')</option>');
            }

            obj.parent().html((obj.parent().hasClass('firstcheckleader') ? '':'<span class="glyphicon glyphicon-arrow-right"></span>') +'<select class="checkleader" style="width:140px" ><option value="0">--选择指定审核人--</option>' + oplist.join('') + '</select>');
            oplist = null;
        }
    });
}

//获取指定审核人名单
function changeCheckLeader(obj){
    if($(obj).val() == "-2"){
        getCheckLeader($(obj));
    }
}

//关闭 modalCaseTypeOperating 时触发
$('#modalCaseTypeOperating').on('hide.bs.modal', function (e) {
    document.getElementById('casetype_name').value = "";
    document.getElementById('casetype_id').value = "-1";
    //$("#casetype_executor").find('option[selected="selected"]').removeAttr("selected");
    $("#casetype_executor").empty();

    $("#firstcheckleader").remove();
    $(".morecheckleader").each(function(){$(this).remove();});
    $(".checkleader").each(function(){$(this).remove();});
    $("#delcheckleader").remove();
    $("#addcheckleader").before('<span class="firstcheckleader"><select class="checkleader" name="firstcheckleader" id="firstcheckleader" style="width:100px" onchange="changeCheckLeader(this);"><option value="-1">默认上级</option><option value = "-2">指定人选</option></select></span>');
})


//关闭 modalCaseTypeDelete 时触发
$('#modalCaseTypeDelete').on('hide.bs.modal', function (e) {
    //Do something
})


// 提交表单数据
function addCaseType(){

    var var_casetype_id = $("#casetype_id").val();
    if(var_casetype_id == '-1'){
        var post_type = "addCaseType";
    }else{
        var post_type = "editCaseType";
    }

    var var_casetype_name = $("#casetype_name").val();
    if(var_casetype_name == ''){
        alert("请填写工单类型名称");
        $("#casetype_name").focus();
        return false;
    }

    var casetype_executor_val = $("#casetype_executor").find("option:selected").val();
    //var casetype_executor_text = $("#casetype_executor").find("option:selected").text();
    if(casetype_executor_val == '0'){
        alert("请选择处理人");
        $("#casetype_executor").focus();
        return false;
    }


    var checkleaderarr =[];
    $(".checkleader").each(function(){
        if($(this).is('select')){
            //alert($(this).find("option:selected").text())
            //alert($(this).find("option:selected").val())
            var tmp_checkleader_var = $(this).find("option:selected").val()
            //var tmp_checkleader_text = $(this).find("option:selected").text()
            if(tmp_checkleader_var == '0'){
                alert("请选择指定审核人");
                $(this).focus();
                return false;
            }
            checkleaderarr.push(tmp_checkleader_var);
        }
    });
    var var_checkleader = checkleaderarr.join(',');
    //alert(var_checkleader);
    //alert(var_casetype_name+casetype_executor_val+var_checkleader);

    $.ajax({
        url: '/case/type/',
        type: "POST",
        dataType: "json",
        data:{'oper':post_type,'casetype_id':var_casetype_id,'casetype_name':var_casetype_name,'casetype_executor':casetype_executor_val,'casetype_checkleader':var_checkleader},
        error: function () {
            alert(post_type +" error");
        },
        success: function (data) {
            //alert("ok");

            $('#modalCaseTypeOperating').modal('hide');
            jQuery(casetype_grid).jqGrid('setGridParam', {}).trigger("reloadGrid");
        }
    });
}

// 编辑工单类型
function editCaseType(typeid){

    getUsers();
    document.getElementById('casetype_id').value = typeid ;

    $.ajax({
        url: '/case/type/',
        type: "POST",
        dataType: "json",
        data:{'oper':"getCaseType",'casetype_id':typeid},
        error: function () {
            alert("getCasetype error");
        },
        success: function (data) {
            //alert(data['id']+" , "+data['name']);
            document.getElementById('casetype_name').value = data['name'];
            for(i in data['executor']){
                var executor = data['executor'][i]
                type_executor_val = executor.split("_")[0]
                $("#casetype_executor").find("option[value='"+type_executor_val+"']").attr("selected",true);
            }

            var oplist = new Array();
            for(key_num in data['users']){
                oplist.push('<option value="' + data['users'][key_num]['id'] + '">' + data['users'][key_num]['cnname'] + '(' + data['users'][key_num]['name']  + ')</option>');
            }

            $("#firstcheckleader").remove();
            var i = 0
            for( j in data['checkleader']){
                //alert(data['checkleader'][j]);
                var checkleader = data['checkleader'][j];
                var user_id = checkleader.split("_")[0]
                var userinfo = checkleader.split("_")[1]

                if(user_id=="-1"){
                    if(i == 0){
                        $("#addcheckleader").before('<span class="firstcheckleader"><select class="checkleader" name="firstcheckleader" id="firstcheckleader" style="width:100px" onchange="changeCheckLeader(this);"><option value="-1" selected>默认上级</option><option value = "-2">指定人选</option></select></span>');
                    }else{
                        $("#addcheckleader").before('<span class="morecheckleader"><span class="glyphicon glyphicon-arrow-right"></span><select class="checkleader" onchange="changeCheckLeader(this);" style="width: 140px"> <option value="-1" selected>默认上级</option><option value = "-2">指定人选</option></select></span>');
                    }

                }else{

                    if(i == 0){
                        $("#addcheckleader").before('<span class="firstcheckleader"><select class="checkleader" name="firstcheckleader" id="firstcheckleader" style="width:140px" onchange="changeCheckLeader(this);"><option value="0">--选择指定审核人--</option>'+ oplist.join('') + '</select></span>');
                        $("#firstcheckleader").find("option[value='"+user_id+"']").attr("selected",true);
                    }else{
                        $("#addcheckleader").before('<span class="morecheckleader"><span class="glyphicon glyphicon-arrow-right"></span><select class="checkleader" name="checkleader_' + i + '" id="checkleader_' + i + '" onchange="changeCheckLeader(this);" style="width: 140px"><option value="0">--选择指定审核人--</option>'+ oplist.join('') + '</select></span>');

                        $("#checkleader_"+i).find("option[value='"+user_id+"']").attr("selected",true);
                    }

                }

                i = i + 1
            }

            if(i>1){
                if($("#addcheckleader").next().is("a")) {
                }else{
                    $("#addcheckleader").after('<a class="btn btn-xs btn-primary" onclick="delCheckLeaderCSS(this)" style="margin-left: 5px" id="delcheckleader">删除一级</a>')
                }
            }

        }
    });
}

// 删除工单类型
function delCaseType(typeid,typename){
    document.getElementById('casetype_id_list').value = typeid ;
    $("#suredellist").html('<li class="text-danger"><b> ID: </b>'+typeid+' ; <b>类型名称: </b>'+typename+'</li>')
};

function sureDelCaseType(){

    var var_type_id_list = $("#casetype_id_list").val();

    $.ajax({
        url: '/case/type/',
        type: "POST",
        dataType: "json",
        data:{'oper':'delCaseType','casetype_ids':var_type_id_list},
        error: function () {
            alert("xxx");
        },
        success: function (data) {
            //alert("ok");
            $('#modalCaseTypeOperating').modal('hide');
            jQuery(casetype_grid).jqGrid('setGridParam', {}).trigger("reloadGrid");
        }
    });

    $('#modalCaseTypeDelete').modal('hide');
}

// search
var timeoutHnd;
var flAuto = false;
function doSearch(ev) {
    if(!flAuto){
      return;
    };

    if(timeoutHnd){
        clearTimeout(timeoutHnd);
    }

    timeoutHnd = setTimeout(gridReload, 1000);
}

function gridReload(){
    var search_enname = jQuery("#search_enname").val()||"";
    var search_cnname = jQuery("#search_cnname").val()||"";
    jQuery(casetype_grid).jqGrid('setGridParam', {
        url : "/case/type/?type=search&search_enname=" + search_enname+"&search_cnname="+search_cnname,
        page : 1
    }).trigger("reloadGrid");
}

function enableAutosubmit(state) {
    flAuto = state;
    jQuery("#searchButton").attr("disabled", state);
}