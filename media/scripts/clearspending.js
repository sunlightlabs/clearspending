$().ready(function() {
	$("#sidenav li p").hide();
   $("#sidenav a").click(function(){
       $("div#stage img").attr("src", this.href);
       //$(this).addClass("active").parent().siblings("li").find("a").removeClass("active");
       $("#sidenav li a").removeClass("active");
       $(this).addClass("active");
       $("#sidenav li p").hide();
       $(this).siblings("p").slideDown("fast").fadeIn("slow");
       return false;
   });
});
