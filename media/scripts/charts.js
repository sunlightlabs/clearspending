
$(function(){

    var chart;

    $(document).ready(function(){

        chart = new Highcharts.Chart({
            chart: {
                renderTo: 'chart',
                type: 'arearange'
            },
            rangeSelector: {
                enabled: false
            },
            tooltip: {
                enabled: true
            },
            title: {
                text: 'Consistency of Reporting'
            },
            xAxis: {
                categories: programs2010,
                labels: {
                    enabled: false
                }
            },
            yAxis: {
                type: 'logarithmic',
                title: {
                    text: 'Mis-reported spending'
                }
            },
            plotOptions: {
                arearange: {
                    //stacking: 'normal',
                    dataLabels: {
                        enabled: false
                    },
                    borderWidth: 0,
                    pointWidth: 1,
                    pointPadding: 1
                }
            },
            series: [
                {
                    name: 'Mis-reported',
                    data: delta_area
                },
            ]
        });
    });
});
