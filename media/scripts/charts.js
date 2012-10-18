$(document).ready(function(){

    var initials = function (name) {
        var first_clause = function (s) {
            return s.split(',')[0];
        };
        var first_letter = function (s) {
            return s.substr(0, 1);
        };
        var bad_words = function (s) {
            return ["of", "for", "and", "the", "United", "States"].indexOf(s) < 0;
        };

        return first_clause(name).split(/\s+/g)
                                 .filter(bad_words)
                                 .map(first_letter)
                                 .join('');
    };


    var width = 840;
    var height = 500;

    var treemap = d3.layout.treemap()
                    .size([width, height])
                    .sticky(true)
                    .value(function(d){ return d.size; });

    var div = d3.select("#chart")
                .append("div")
                .style("position", "relative")
                .style("width", width + "px")
                .style("height", height + "px");

    var cell = function () {
        this.style("left", function(d){ return d.x + "px"; })
            .style("top", function(d){ return d.y + "px"; })
            .style("width", function(d){ return Math.max(0, d.dx - 1) + "px"; })
            .style("height", function(d){ return Math.max(0, d.dy - 1) + "px"; });
    };

    div.data([pro_flare])
       .selectAll("div")
       .data(treemap.nodes)
       .enter()
       .append("div")
       .on("mouseover", function(d){
           if (d.children) {
               console.log(this);
           } else {
               var ag_prefix = d.program_number.split('.')[0];
               var ag_name = agencies[ag_prefix];
               var ag_inits = initials(ag_name);
               $("#program-description").text(d.program_name + ' (CFDA program ' + d.program_number + '), ' + ag_name);
               $("#status, #program-description").toggle();
           }
       })
       .on("mouseout", function(d){
           if (d.children) {
           } else {
               $("#status, #program-description").toggle();
           }
       })
       .on("click", function(d){
           window.location.href = '/clearspending/program/' + d.program_number + '/pct/';
       })
       .attr("class", function(d){
            if (d.non == -100.0) {
                return 'cell blind';
            } else if ((d.over >= 50.0) || (d.under >= 50.0)) {
                return 'cell fail';
            } else if ((d.over >= 0) || (d.under >= 0)) {
                return 'cell pass';
            } else {
                return 'cell unknown';
            }
       })
       .call(cell);

    
    console.log(pro_flare);
});
