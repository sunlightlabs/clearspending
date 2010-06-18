$().ready(function() {
	$("#sidenav li p").hide();
   $("#sidenav a").click(function(){
       $("div#stage img").attr("src", this.href);
       //$(this).addClass("active").parent().siblings("li").find("a").removeClass("active");
       $("#sidenav li a").removeClass("active");
       $(this).addClass("active");
       $("#sidenav li p").hide("slow");
       $(this).siblings("p").show("slow");
       return false;
   });
	$("a.expand").toggle(
	  function(){
	     $(this).addClass("expanded").siblings("p").slideDown("slow");
	  },
	  function(){
  	     $(this).removeClass("expanded").siblings("p").slideUp("slow");
  	  } 
	);
});