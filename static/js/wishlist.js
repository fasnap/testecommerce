$(document).ready(function() {
    $(document).on('click',".add-wishlist",function(){
        var _pid=$(this).attr('data-product');
        var _vm=$(this)
        console.log(_pid);
        $.ajax({
            url:"/store/add_wishlist",
            data:{
                product:_pid
            },
            dataType:'json',
            success:function(res){
                console.log(res);
                if(res.bool==true){
                    _vm.addClass('disabled').removeClass('add-wishlist');
                }
            }
        })
        
    });
});