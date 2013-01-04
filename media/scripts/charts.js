var agencies = {
    '10': 'Department of Agriculture',
    '11': 'Department of Commerce',
    '12': 'Department of Defense',
    '14':'Department of Housing and Urban Development',
    '15': 'Department of the Interior',
    '16':'Department of Justice',
    '17': 'Department of Labor',
    '19': 'U.S. Department of State',
    '20':'Department of Transportation',
    '21':'Department of the Treasury',
    '23':'Appalachian Regional Commission',
    '27':'Office of Personnel Management',
    '29':'Commission on Civil Rights',
    '30':'Equal Employment Opportunity Commission',
    '31':'Export Import Bank of the United States',
    '32':'Federal Communications Commission',
    '33':'Federal Maritime Commission',
    '34': 'Federal Mediation and Concillation Service',
    '36':'Federal Trade Commission',
    '39':'General Services Administration',
    '40': 'Government Printing Office',
    '42':'Library of Congress',
    '43':'National Aeronautics and Space Administration',
    '44':'National Credit Union Administration',
    '45':'National Endowment for the Arts',
    '46':'National Labor Relations Board',
    '47':'National Science Foundation',
    '57':'Railroad Retirement Board',
    '58':'Securities and Exchange Commission',
    '59':'Small Business Administraton',
    '64':'Department of Veterans Affairs',
    '66':'Environmental Protection Agency',
    '68':'National Gallery of Art',
    '70':'Overseas Private Investment Corporation',
    '77':'Nuclear Regulatory Commission',
    '78':'Commodity Futures Trading Commission',
    '81':'Department of Energy',
    '84':'Department of Education',
    '85': 'Various Scholarship and Fellowship Foundations',
    '86':'Pension Benefit Guaranty Corporation',
    '88':'Architectural and Transportation Barriers Compliance Board',
    '89':'National Archives and Records Administration',
    '90':'Denali Commission, Delta Regional Authority, Japan US Friendship Commission, US Election Assistance Commission, Broadcasting Board of Governors',
    '91':'United States Institute of Peace',
    '93':'Department of Health and Human Services',
    '94':'Corporation for National and Community Service',
    '95': 'Executive Office of the President',
    '96':'Social Security Administration',
    '97':'Department of Homeland Security',
    '98':'United States Agency for International Development'
};

var short_agency_names = {
    '10': 'Agriculture',
    '11': 'Commerce',
    '12': 'Defense',
    '14': 'Housing',
    '15': 'Interior',
    '16': 'Justice',
    '17': 'Labor',
    '19': 'State',
    '20': 'Transportation',
    '21': 'Treasury',
    '23': 'Appalachian Comm.',
    '27': 'Office of Personnel Management',
    '29': 'Commission on Civil Rights',
    '30': 'Equal Employment Opportunity Commission',
    '31': 'Export Import Bank',
    '32': 'FCC',
    '33': 'Federal Maritime Commission',
    '34': 'Federal Mediation and Concillation Service',
    '36': 'Federal Trade Commission',
    '39': 'General Services Administration',
    '40': 'Government Printing Office',
    '42': 'Library of Congress',
    '43': 'NASA',
    '44': 'NCUA',
    '45': 'NEA',
    '46': 'NLRB',
    '47': 'NSF',
    '57': 'Railroad Retirement Board',
    '58': 'SEC',
    '59': 'Small Business',
    '64': 'Veterans Affairs',
    '66': 'EPA',
    '68': 'National Gallery of Art',
    '70': 'OPIC',
    '77': 'NRC',
    '78': 'CFTC',
    '81': 'Energy',
    '84': 'Education',
    '85': 'Various Scholarship and Fellowship Foundations',
    '86': 'Pension Benefit Guaranty Corp.',
    '88': 'Architectural and Transportation Barriers Compliance Board',
    '89': 'National Archives',
    '90': 'Other',
    '91': 'Institute of Peace',
    '93': 'HHS',
    '94': 'Community Service',
    '95': 'Office of the President',
    '96': 'Social Security',
    '97': 'Homeland Security',
    '98': 'USAID'
};

var zip_arrays = function () {
    var args = [].slice.call(arguments);
    var longest = args.reduce(function(a,b){
        return a.length>b.length ? a : b
    }, []);

    return longest.map(function(_,i){
        return args.map(function(array){return array[i]})
    });
};

var transform = function () {
    if ((arguments.length === 0) || ((arguments.length === 1) && (arguments[0].length === 0))) {
        return "";
    }

    var transforms = ["scale", "translate", "matrix", "rotate", "skewX", "skewY"];
    var is_transform = function (s) {
        return transforms.indexOf(s) !== -1;
    };

    var ix = 0;
    var args = Array.apply(null, arguments);
    var arg_pairs = zip_arrays(args, args.slice(1));
    var rope = arg_pairs.map(function(pair){
        var curr = pair[0];
        var next = pair[1];

        if (curr === undefined)
            throw "undefined transform argument";

        if (is_transform(curr)) {
            if (is_transform(next) || (next === undefined)) {
                return [curr, "() "];
            } else {
                return [curr, "("];
            }
        } else {
            if (is_transform(next) || (next === undefined)) {
                return [curr.toString(), ") "];
            } else {
                return [curr.toString(), ","];
            }
        }
    });

    rope = rope.reduce(function(a, b) {
        return a.concat(b);
    });
    return rope.join("").trim();
};

$(document).ready(function(){

    var itemgetter = function (k) {
        return function (o) {
            return o[k];
        };
    };

    var identity = function (x) {
        return x;
    };

    var fn_sequence = function () {
        var args = arguments;
        return function(){
            var ret = null;
            for (var ix = 0; ix < args.length; ix++) {
                ret = args[ix].apply(this, arguments);
            }
            return ret;
        }
    };

    var short_money = function (n) {
        var sizes = [
            ['trillion', Math.pow(10, 12)],
            ['billion', Math.pow(10, 9)],
            ['million', Math.pow(10, 6)],
            ['thousand', Math.pow(10, 3)]
        ];
        for (var ix = 0; ix < sizes.length; ix++) {
            var label = sizes[ix][0];
            var dollars = sizes[ix][1];
            if (n >= dollars) {
                short_n = Math.round(n / dollars, 2);
                return "$" + short_n.toString() + " " + label;
            }
        }
        return "$" + n
    };

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

    var default_chart_year = function () {
        var years = $(".fiscal_year_chooser").map(function(){ return $(this).text(); });
        var max_year = Math.max.apply(null, years);
        return max_year;
    };


    var consistency_treemap = function (options) {
        var options = options || {};
        var default_to = function (opt, val) { options[opt] = options[opt] || val; };
        default_to("width", 840);
        default_to("height", 520);
        default_to("element", "#chart");

        var cell = function (d, i) {
            this.style("left", function(d){ return d.x + "px"; })
                .style("top", function(d){ return d.y + "px"; })
                .style("width", function(d){ return Math.max(0, d.dx - 1) + "px"; })
                .style("height", function(d){ return Math.max(0, d.dy - 1) + "px"; });
        };

        var show_program_label = function (d) {
            if (d.children) {
                /* no-op */
            } else {
                var ag_prefix = d.number.split('.')[0];
                var ag_name = agencies[ag_prefix];
                var ag_inits = initials(ag_name);
                $("#program-description").text(d.title
                                               + " (CFDA program "
                                               + d.number
                                               + "), "
                                               + ag_name
                                               + ": "
                                               + short_money(d.size)
                                               );
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

                var flare_url = "../static/data/consistency_flare_" + fiscal_year + "_categories.json";
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
                           window.location.href = program_url(d.number);
                       })
                       .attr("class", classify_datum)
                       .attr("id", id_from_program_number)
                       .call(cell);

                    map.exit().remove();

                    var shell_background = function (cls) {
                        var $inner = $("#chart > div");
                        var $cells = $("." + cls, $inner);
                        var left = Math.min.apply(null, $cells.map(function(ix,n){ return $(n).position().left; }));
                        var top = Math.min.apply(null, $cells.map(function(ix,n){ return $(n).position().top; }));
                        var right = Math.max.apply(null, $cells.map(function(ix,n){ return $(n).position().left + $(n).width(); }));
                        var bottom = Math.max.apply(null, $cells.map(function(ix,n){ return $(n).position().top + $(n).height(); }));
                        var $shell = $("<div></div>").css("position", "absolute")
                                                     .css("top", top + "px")
                                                     .css("left", left + "px")
                                                     .css("width", right - left + "px")
                                                     .css("height", bottom - top + "px")
                                                     .css("z-index", -99999)
                                                     .addClass(cls)
                                                     .addClass("bg-shell")
                                                     .prependTo($inner);
                    };
                    shell_background("fail");
                    shell_background("pass");
                    shell_background("blind");
                    shell_background("perfect");
                });
            }, 0);

            $(".fiscal_year_chooser").each(function(){
                $(this).removeClass("selected");
                var year = parseInt($(this).text());
                if (year == fiscal_year) {
                    $(this).addClass("selected");
                }
            });
        };

        $(".fiscal_year_chooser").click(function(event){
            show_consistency_flare(parseInt($(this).text()));
        });
        
        show_consistency_flare(default_chart_year());
    };

    var timeliness_chart = function (options) {
        var options = options || {};
        var default_to = function (opt, val) { options[opt] = options[opt] || val; };
        default_to("width", 580);
        default_to("height", 380);
        default_to("axisPadding", 30);
        default_to("element", "#chart");


        var show_agency_label = function (d) {
            var early_or_late = ((d.delta_rows >= 0) ? "late" : "early");
            $("#days-delta").html(
                + Math.abs(d.delta_rows)
                + " days "
                + early_or_late
            ).attr("class", ((d.delta_rows >= 0) ? "fail" : "pass"));
            $("#program-description").html(d.title);
            $("#status, #program-description, #days-delta").toggle();
        };

        var reset_agency_label = function (d) {
            $("#status, #program-description, #days-delta").toggle();
        };

        var show_timeliness_chart = function (fiscal_year) {
            $(options["element"]).css("width", options["width"]).css("height", options["height"]).empty().append('<div class="chart-loading"></div>');
            setTimeout(function(){
                var flare_url = "" + fiscal_year + "/";
                d3.json(flare_url, function(json){
                    var records = json.agencies;
                    records.forEach(function(d){
                        d['delta_rows'] = d.lag_rows - 30;
                        d['delta_dollars'] = d.lag_dollars - 30;
                    });

                    records.sort(function(a,b){ return a.delta_rows - b.delta_rows; });

                    var chart = d3.select(options['element'])
                                  .append("svg")
                                  .attr("id", "timeliness-art")
                                  .style("width", options["width"] + "px")
                                  .style("height", options["height"] + "px");

                    var x = d3.scale
                              .ordinal()
                              .rangeRoundBands([options["axisPadding"], options["width"] - options["axisPadding"]], 0.1)
                              .domain(records.map(function(d){ return d.title; }));

                    var y_min = d3.min(records.map(function(d){ return d.delta_rows; }));
                    var y_max = d3.max(records.map(function(d){ return d.delta_rows; }));
                    var y = d3.scale
                              .linear()
                              .range([options["axisPadding"], options["height"] - options["axisPadding"]])
                              .domain([json.earliest - 30, json.latest - 30]);
                    var on_time_xcoord = y(0);

                    var bars = chart.selectAll("g.bar")
                                    .data(records)
                                    .enter()
                                    .append("g")
                                    .attr("data-agency-code", function(d){ return d.number; })
                                    .attr("data-agency-name", function(d){ return d.title; })
                                    .attr("class", "bar")
                                    .attr("transform", function(d){
                                        return "translate(X, 0)".replace("X", '' + x(d.title));
                                    })
                                    .on("mouseover", show_agency_label)
                                    .on("mouseout", reset_agency_label);

                    bars.append("rect")
                        .attr("x", 0)
                        .attr("y", 0)
                        .attr("fill", "none")
                        .attr("pointer-events", "all")
                        .attr("height", options["height"])
                        .attr("width", x.rangeBand());

                    bars.append("rect")
                        .attr("class", function(d){
                            if (d.delta_rows > 0) {
                                return "bar fail";
                            } else {
                                return "bar pass";
                            }
                        })
                        .attr("x", 0)
                        .attr("y", function(d){
                            if (d.delta_rows > 0) {
                                return on_time_xcoord - 1;
                            } else {
                                return y(d.delta_rows) - 1;
                            }
                        })
                        .attr("height", function(d){
                            if (d.delta_rows > 0) {
                                return y(d.delta_rows) - on_time_xcoord + 2;
                            } else {
                                return on_time_xcoord - y(d.delta_rows) + 2;
                            }
                        })
                        .attr("width", x.rangeBand());

                    var neg_axis = d3.svg.axis()
                                         .scale(y)
                                         .orient("left")
                                         .tickValues([Math.min.apply(null, y.domain())]);

                    var pos_axis = d3.svg.axis()
                                         .scale(y)
                                         .orient("right")
                                         .tickValues([y_max]);

                    var early_block = chart.append("g")
                         .attr("id", "early-annotation")
                         .attr("transform", "translate(X, Y)".replace("X", x.range()[0]).replace("Y", Math.round(y(y_min)) - 2));
                    early_block.append("text")
                               .attr("x", 70)
                               .text(Math.abs(y_min) + " days early");
                    early_block.append("line")
                               .attr("stroke", "black")
                               .attr("strokeWidth", 1)
                               .attr("x1", 0)
                               .attr("x2", 70)
                               .attr("y1", 0)
                               .attr("y2", 0);

                    var late_block = chart.append("g")
                                          .attr("id", "late-annotation")
                                          .attr("transform", "translate(X, Y)".replace("X", x.range().slice(-1)[0] + x.rangeBand() - 50).replace("Y", Math.round(y(y_max)) + 2));
                    late_block.append("text")
                              .attr("x", 0)
                              .text(Math.abs(y_max) + " days late");
                    late_block.select("text")
                              .attr("dx", function(d){
                                  return "-" + this.getComputedTextLength();
                              });
                    late_block.append("line")
                              .attr("stroke", "black")
                              .attr("stroke-width", 1)
                              .attr("x1", 0)
                              .attr("x2", 50)
                              .attr("y1", 0)
                              .attr("y2", 0);
                });

            }, 0);

            $(".fiscal_year_chooser").each(function(){
                $(this).removeClass("selected");
                var year = parseInt($(this).text());
                if (year == fiscal_year) {
                    $(this).addClass("selected");
                }
            });
        };

        $(".fiscal_year_chooser").click(function(event){
            show_timeliness_chart(parseInt($(this).text()));
        });

        show_timeliness_chart(default_chart_year());
    };


    var completeness_diagram = function (options) {
        var options = options || {};
        var default_to = function (opt, val) { options[opt] = options[opt] || val; };
        default_to("width", 840);
        default_to("height", 480);
        default_to("text_width", 105);
        default_to("min_opacity", 0.5);
        default_to("max_opacity", 1.0);
        default_to("element", "#chart");

        var show_cell_details = function (d, col, target) {
            var val = d[col] || 0;
            var pct_col = "" + col + "_pct";
            var pct_val = d[pct_col] || 0;

            var tmpl = $("#cell-details-tmpl").html();
            tmpl = tmpl.replace("__agency__", d.agency__name);
            tmpl = tmpl.replace("__column__", col);
            tmpl = tmpl.replace("__totaldollars__", short_money(d.total_dollars));
            tmpl = tmpl.replace("__faileddollars__", short_money(d.failed_dollars));
            tmpl = tmpl.replace("__val__", short_money(val));
            tmpl = tmpl.replace("__pct__", Math.round(pct_val * 100, 2));
            $(target).html(tmpl);

            if (val == 0) {
                $(target).addClass("pass");
                $(target).removeClass("fail");
            } else {
                $(target).addClass("fail");
                $(target).removeClass("pass");
            }
            $(target).css("visibility", "visible");
        };

        var reset_program_label = function (d) {
            $("#hovered-details").css("visibility", "hidden");
        };

        var hover_column = function () {
            var column_check = $(this).attr("data-column-check");
            d3.selectAll("svg rect.column-bg").classed("hovered", function(d){
                return $(this).attr("data-column-check") == column_check;
            });
        };

        var hover_bar = function () {
            var agency_code = $(this).attr("data-agency-code");
            d3.selectAll("svg rect.bar-bg").classed("hovered", function(d){
                return d.agency__code == agency_code;
            });
        };

        var hover_cell = function (d) {
            var col = $(this).attr("data-column-check");
            show_cell_details(d, col, "#hovered-details");
        };

        var select_column = function () {
            var column_check = $(this).attr("data-column-check");
            d3.selectAll("svg rect.column-bg").classed("selected", function(d){
                return $(this).attr("data-column-check") == column_check;
            });
        };

        var select_bar = function () {
            var agency_code = $(this).attr("data-agency-code");
            d3.selectAll("svg rect.bar-bg").classed("selected", function(d){
                return d.agency__code == agency_code;
            });
        };

        var select_cell = function (d) {
            var col = $(this).attr("data-column-check");
            show_cell_details(d, col, "#selected-details");
        };

        var unselect_bars_and_columns = function () {
            $("svg rect.bar-bg, svg rect.column-bg").attr("fill", "transparent");
            $("#program-description").hide();
        };

        $(options["element"]).bind("mouseleave", unselect_bars_and_columns);

        var chart = d3.select(options['element'])
                      .append("svg")
                      .attr("id", "timeliness-art")
                      .style("width", options["width"] + "px")
                      .style("height", options["height"] + "px");

        d3.selectAll("#status-con, #chart-con")
          .style("width", options["width"] + "px");

        d3.selectAll("#chart-con")
          .style("height", options["height"] + "px");

        var show_completeness_diagram = function (fiscal_year) {
            $(options["element"]).css("height", options["height"] + "px");
            $("svg", options["element"]).empty();
            setTimeout(function(){
                var url = "" + fiscal_year + "/";
                var generic_compare = function (a, b) {
                    if (a == b) { return 0; }
                    else if (a < b) { return -1; }
                    else { return 1; }
                };
                d3.json(url, function(json){
                    json.forEach(function(d){
                        d['short_name'] = short_agency_names[d.agency__code];
                    });

                    json.sort(function(a,b){
                        return generic_compare(a.short_name, b.short_name);
                    });

                    var y = d3.scale
                              .ordinal()
                              .rangeRoundBands([0, options["height"]], 0.3)
                              .domain(json.map(itemgetter('agency__name')));

                    var col_fields = [
                        'principal_place_state', 'record_type',
                        'cfda_program_num', 'recipient_type',
                        'recipient_state', 'principal_place_cc',
                        'principal_place_code', 'recipient_county_code',
                        'assistance_type', 'federal_funding_amount',
                        'federal_agency_code', 'recipient_city_code',
                        'recipient_county_name', 'recipient_name',
                        'obligation_action_date', 'recipient_cong_district',
                        'recipient_city_name', 'federal_award_id',
                        'action_type' ];
 
                    var x = d3.scale
                              .ordinal()
                              .rangeRoundBands([options["text_width"], options["width"]], 0.15)
                              .domain(["agency__name"].concat(col_fields));

                    chart.selectAll("rect.column-bg")
                         .data(col_fields)
                         .enter()
                         .append("rect")
                         .attr("data-column-check", identity)
                         .attr("class", function(d){ return ["column-bg", d].join(" "); })
                         .attr("x", function(d){ return x(d) - x.rangeBand() * 0.15; })
                         .attr("y", 0)
                         .attr("width", x.rangeBand() * 1.3)
                         .attr("height", options["height"] + "px");

                    chart.selectAll("rect.bar-bg")
                         .data(json)
                         .enter()
                         .append("rect")
                         .attr("class", function(d){ return "bar-bg agency-" + d.agency__code; })
                         .attr("data-agency-code", itemgetter("agency__code"))
                         .attr("x", 0)
                         .attr("y", function(d){ return y(d.agency__name) - y.rangeBand() * 0.15; })
                         .attr("width", options["width"] + "px")
                         .attr("height", y.rangeBand() * 1.30);

                    var bars = chart.selectAll("g.bar")
                                    .data(json)
                                    .enter()
                                    .append("g")
                                    .attr("class", function(d){ return "bar agency-" + d.agency__code; })
                                    .attr("data-agency-code", itemgetter("agency__code"))
                                    .attr("transform", function(d){
                                        return "translate(0, Y)".replace("Y", y(d.agency__name));
                                    });

                    bars.append("rect")
                        .attr("class", "agency-name")
                        .attr("x", x("agency__name"))
                        .attr("y", 0)
                        .attr("width", x.rangeBand())
                        .attr("height", y.rangeBand());

                    bars.append("a")
                        .attr("xlink:href", function(d){ return "../agency/" + d.agency__code + "/" + fiscal_year + "/dollars/"; })
                        .append("text")
                        .attr("class", "agency-name")
                        .attr("x", 1)
                        .attr("y", y.rangeBand() / 2)
                        .attr("dx", "0.6em")
                        .attr("dy", "0.35em")
                        .text(function(d){
                            return d.short_name;
                        });

                    for (var ix = 0; ix < col_fields.length; ix++) {
                        var col = col_fields[ix];
                        var pct_col = col + "_pct";

                        bars.append("rect")
                            .attr("class", function(d){
                                var val = d[pct_col] || 0;
                                var grade = (val == 0) ? "pass" : "fail";
                                return ["column", col,  grade].join(" ");
                            })
                            .on("mouseover", fn_sequence(hover_column, hover_bar, hover_cell))
                            .on("mouseout", reset_program_label)
                            .on("click", fn_sequence(select_column, select_bar, select_cell))
                            .attr("data-column-check", col)
                            .attr("data-agency-code", itemgetter("agency__code"))
                            .attr("x", x(col))
                            .attr("y", 0)
                            .attr("width", x.rangeBand())
                            .attr("height", y.rangeBand())
                            .attr("opacity", function(d){
                                var val_pct = d[pct_col];
                                if (val_pct == null)
                                    val_pct = 0;
                                if (val_pct == 0)
                                    return 1;
                                var opacity_range = (options["max_opacity"]
                                                     - options["min_opacity"]);
                                var opacity = opacity_range * val_pct + options["min_opacity"];
                                return opacity;
                            });

                    }
                });
            }, 0);

            $(".fiscal_year_chooser").each(function(){
                $(this).removeClass("selected");
                var year = parseInt($(this).text());
                if (year == fiscal_year) {
                    $(this).addClass("selected");
                }
            });
        };

        $(".fiscal_year_chooser").click(function(event){
            show_completeness_diagram(parseInt($(this).text()));
        });

        show_completeness_diagram(default_chart_year());
    };


    var venn_diagram = function (options) {
        var options = options || {};
        var default_to = function (opt, val) { options[opt] = options[opt] || val; };
        default_to("size", 840);
        default_to("element", "#chart");

        var circle_data = [
            [-0.19811119,  0.00319773, 0.4828593439062896, "Consistency"],
            [ 0.51264974,  0.00319773, 0.29656219033435582, "Completeness"],
            [ 0.2198261 , -0.20461201, 0.070839795183324353, "Timeliness"]
        ];
        var min_x = circle_data.reduce(function(accum, curr){
            return Math.min(accum, curr[0] - curr[2]);
        }, 1);
        var max_x = circle_data.reduce(function(accum, curr){
            return Math.max(accum, curr[0] + curr[2]);
        }, 0);
        var min_y = circle_data.reduce(function(accum, curr){
            return Math.min(accum, curr[1] - curr[2]);
        }, 1);
        var max_y = circle_data.reduce(function(accum, curr){
            return Math.max(accum, curr[1] + curr[2]);
        }, 0);
        var unit_height = max_y - min_y;
        var unit_width = max_x - min_x;

        var aspect_ratio = unit_width / unit_height;
        var width = (aspect_ratio >= 1) ? options["size"] : options["size"] * aspect_ratio;
        var height = (aspect_ratio <= 1) ? options["size"] : options["size"] / aspect_ratio;
        var scale = height / unit_height;

        var colors = [ "#dec703", "#85BE3D", "#EB4724" ];
        var labels = [ "completeness", "consistency", "timeliness" ];

        var venn = d3.select("svg#venn").attr("width", width)
                                        .attr("height", height);

        venn.select("g").append("rect").attr("fill", "none")
                                       .attr("width", width)
                                       .attr("height", height)
                                       .attr("stroke", "none")
                                       .attr("stroke-width", 1);


        var circles_group = venn.append("g")
                                .attr("id", "circles-group")
                                .attr("transform", transform("scale", scale,
                                                             "translate", Math.abs(min_x), unit_height / 2));

        var circles = circles_group.selectAll("circle")
                                   .data(circle_data);

        circles.enter()
               .append("circle")
               .attr("fill", function(d){ return colors.shift(); })
               .attr("opacity", 0.5)
               .attr("r", function(d){ return d[2]; })
               .attr("cx", function(d){ return d[0]; })
               .attr("cy", function(d){ return d[1]; });

        circles.exit().remove();
    };

    if ($("body.consistency").length > 0) {
        consistency_treemap({
        	"width": 890,
            "height": 380,
        });
    };
    if ($("body.timeliness").length > 0) {
        timeliness_chart({
            "width": 580,
            "height": 380,
            "axisPadding": 15
        });
    };
    if ($("body.completeness").length > 0) {
        completeness_diagram({
            "width": (/narrow/.test(window.location.href)) ? 550 : 840,
            "min_opacity": 0.50,
            "max_opacity": 1.00
        });
    };
    if ($("body.home").length > 0) {
        venn_diagram({
            "size": 500
        });
    };
});
