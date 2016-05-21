

// 添加审核人
function addreviewer(obj){
    if($(obj).prev().is("select")){
        var preval = $(obj).prev().val();
    }else if($(obj).prev().is("span")){
        var preval = $(obj).prev().find(".reviewer").val();
    }
    var hasboss = false;
    $(".reviewer").each(function(){
        if($(this).val() == "-1"){
            hasboss = true;
        }
    })
    if(hasboss == true){  //如果前面出现了上级领导  那么后面只能是指定人选了
        var len = $(".reviewer").length;
        $(obj).before('<span class="morereviewer"><span class="glyphicon glyphicon-arrow-right"></span><select class="reviewer" id="reviewer_'+len+'" onchange="changeReviewer(this);" style="width: 100px" num="0"><option value = "-2">指定人选</option></select></span>');
        getreviewer($("#reviewer_"+len));
    }else{
        $(obj).before('<span class="morereviewer"><span class="glyphicon glyphicon-arrow-right"></span><select class="reviewer" onchange="changeReviewer(this);" style="width: 100px" num="0"> <option value="-1">默认上级</option><option value = "-2">指定人选</option></select></span>')
    }
    if($(obj).next().is("a")) {
    }else{
        $(obj).after('<a class="btn btn-xs btn-primary" onclick="delReviewer(this)" style="margin-left: 5px" id="delreviewer">删除一级</a>')
    }
}

// 删除一级
function delReviewer(obj){
    if($(obj).prev().prev().is("span") && $(obj).prev().prev().prev().is("select")){
        $(obj).prev().prev().remove();
        $(obj).remove();
    }else if($(obj).prev().prev().is("span") && $(obj).prev().prev().prev().is("span")){
        $(obj).prev().prev().remove();
    }
    if($(obj).prev().prev().hasClass("firstreviewer")){
        $(obj).remove();
    }
}


// 获取审核人名单
function getreviewer(obj){
	alert("xx");
    $.ajax({
        url: '/tickettype/',
        type: "POST",
        dataType: "json",
        data:{'type':"getreviewer"},
        error: function () {
        },
        success: function (data) {
        	alert(data);
            // var oplist = new Array();
            // for (var i = 0; i < data.count; i++) {
            //     var _info = data.items[i];
            //     oplist.push('<option value="' + _info.id + '">' + _info.cname + '(' + _info.username + ')</option>');
            // }
            // if(obj.parent().hasClass('firstleader')){
            //    var  len = 0;
            // }else{
            //     var len= $(".sureLeaderAuth_select").length;
            // }
            // obj.parent().html((obj.parent().hasClass('firstleader') ? '':'<span class="glyphicon glyphicon-arrow-right"></span>') +'<select name = "sureLeaderAuth_select" class="sureLeaderAuth_select"  onchange="sureLeaderAuth(this)" style="width: 170px" num="0" id="sureLeaderAuth_select_'+len+'"><option value="">--选择固定审核人--</option>' + oplist.join('') + '</select>');
            // $("#sureLeaderAuth_select_"+len).select2();
            // $("#jNotify").click();
            // oplist = null;
        }
    });
	
}

//获取审核指定审核人名单
function changeReviewer(obj){
    if($(obj).val() == "-2"){
        getreviewer($(obj));
    }
}


//固定人员的选择后操作
function sureLeaderAuth(obj){
    $(obj).parent().html(($(obj).parent().hasClass('firstleader') ? '':'<span class="glyphicon glyphicon-arrow-right"></span>') +'<span class="leaders" leaderid='+$(obj).val()+'>'+$(obj).find("option:selected").text()+'</span>');
}

// 编辑工单类型
function show_edit_modal(){

}


//
function add(){

    var reviewerarr =[];
    $(".reviewer").each(function(){
        if($(this).is('select')){
            leadersarr.push($(this).val());
        }else if($(this).is('span')){
            leadersarr.push($(this).attr('reviewerid'));
        }
    })
    var reviewer = reviewerarr.join(',');
	
}


