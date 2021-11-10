//Activate selected address
$(document).ready(function() {
    $(document).on('click', '.activate-address', function(event){
        console.log(event);
        var _aId=$(this).attr('data-address');
        var _vm=$(this);
        //ajax
        $.ajax({
            url:'/activate-address',
            data:{
                'id':_aId,
            },
            dataType:'json',
            
            success:function(res){
                if(res.bool==true){
                    $(".address").removeClass('shadow boarder-secondary');
                    $(".address"+_aId).addClass('shadow boarder-secondary');
                    $(".check").hide();
                    $(".actbtn").show();
               
                    $(".check"+_aId).show();
                    $(".btn"+_aId).hide();
                    
                    
                    location.reload()
                }
            }       
        });
     

      });
 
    
});



