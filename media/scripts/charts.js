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

    var consistency_treemap = function (options) {
        var options = options || {};
        var default_to = function (opt, val) { options[opt] = options[opt] || val; };
        default_to("width", 840);
        default_to("height", 520);
        default_to("element", "#chart");

        var cell = function () {
            this.style("left", function(d){ return d.x + "px"; })
                .style("top", function(d){ return d.y + "px"; })
                .style("width", function(d){ return Math.max(0, d.dx - 1) + "px"; })
                .style("height", function(d){ return Math.max(0, d.dy - 1) + "px"; });
        };

        var show_program_label = function (d) {
            if (d.children) {
                console.log(this);
            } else {
                var ag_prefix = d.number.split('.')[0];
                var ag_name = agencies[ag_prefix];
                var ag_inits = initials(ag_name);
                $("#program-description").text(d.title + " (CFDA program " + d.number + "), " + ag_name);
                $("#status, #program-description").toggle();
            }
        };

        var reset_program_label = function (d) {
            if (d.children) {
            } else {
                $("#status, #program-description").toggle();
            }
        };

        var classify_datum = function (d) {
            if (d.non == -100.0) {
                return 'cell blind';
            } else if ((d.over >= 50.0) || (d.under >= 50.0)) {
                return 'cell fail';
            } else if ((d.over >= 0) || (d.under >= 0)) {
                return 'cell pass';
            } else if (d.children == null) {
                return 'cell perfect';
            } else {
                return 'cell category';
            }
        };

        var id_from_program_number = function (d) {
            if (d.children) {
                return "category_" + d.name;
            } else {
                return "program_" + d.number.toString().replace(".", "_");
            }
        };

        var show_consistency_flare = function (fiscal_year) {
            $(options["element"]).css("width", options["width"]).css("height", options["height"]).empty().append('<div class="chart-loading"><div>Loading...</div></div>');

            setTimeout(function(){

            var flare_url = "/static/data/consistency_flare_" + fiscal_year + "_categories.json";
            d3.json(flare_url, function(json){
                var treemap = d3.layout.treemap()
                                .size([options["width"], options["height"]])
                                .sticky(true)
                                .value(function(d){ return d.size; });

                $(options["element"]).empty();

                var chart = d3.select(options['element'])
                              .append("div")
                              .style("position", "relative")
                              .style("width", options["width"] + "px")
                              .style("height", options["height"] + "px");

                var map = chart.data([json])
                               .selectAll("div")
                               .data(treemap.nodes);

                map.enter()
                   .append("div")
                   .on("mouseover", show_program_label)
                   .on("mouseout", reset_program_label)
                   .on("click", function(d){
                       window.location.href = "/program/" + d.number + "/pct/";
                   })
                   .attr("class", classify_datum)
                   .attr("id", id_from_program_number)
                   .call(cell);

                map.exit().remove();

                $("span.fiscal_year_chooser").each(function(){
                    $(this).removeClass("selected");
                    var year = parseInt($(this).text());
                    if (year == fiscal_year) {
                        $(this).addClass("selected");
                    }
                });
            });

            }, 0);
        };

        var years = $("span.fiscal_year_chooser").map(function(){ return $(this).text(); });
        var max_year = Math.max.apply(null, years);
        show_consistency_flare(max_year);

        $("span.fiscal_year_chooser").click(function(event){
            show_consistency_flare(parseInt($(this).text()));
        });
    };

    consistency_treemap();
});
