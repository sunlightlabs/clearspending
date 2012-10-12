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
       .attr("class", "cell")
       .style("background", function(d){
            if (d.non == -100.0) {
                return '#000000';
            } else if ((d.over >= 50.0) || (d.under >= 50.0)) {
                return 'rgb(240, 59, 32)';
            } else if ((d.over >= 0) || (d.under >= 0)) {
                return 'rgb(255, 237, 160)';
            } else {
                return '#ffffff';
            }
       })
       .call(cell)
       .text(function(d){ return d.children ? null : d.name });

    console.log(pro_flare);
});
