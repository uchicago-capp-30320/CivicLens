// graph.js

export function drawGraph() {
    // set up
    const margin = { top: 10, right: 100, bottom: 20, left: 150, middle: 20};

    const width = document.getElementById("chart").clientWidth - margin.left - margin.right;
    const height = document.getElementById("chart").clientHeight - margin.top - margin.bottom;

    const svg = d3.select('#chart')
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // Data
    const stringData = document.getElementById('topics').innerHTML;
    const validJSONString = stringData.replace(/'/g, '"');
    let data = JSON.parse(validJSONString);

    // add total attributes
    data = data.map(d => {
        d.total = d.positive + d.neutral + d.negative;
        // d.positive_freq = d.positive/d.total;
        // d.neutral_freq = d.neutral/d.total;
        // d.negative_freq = d.negative/d.total;
        return d;
    });

    console.log(data);

    const sentiment_counts = Object.keys(data[0]).filter(d => ((d != "topic") & (d != "source") & (d != "total")));
    const topics = data.map(d => d.topic);
    const stackedData = d3.stack().keys(sentiment_counts)(data);
    const xMax = d3.max(stackedData[stackedData.length - 1], d => d[1]);
    
    // Define scales for totals chart
    const xTotals = d3.scaleLinear()
    .domain([0, xMax])
    .range([0, width/2]);

    const yTotals = d3.scaleBand()
    .domain(topics)
    .range([0, height])
    .padding(0.3);

    // Define scales for percentage chart
    const xPercentage = d3.scaleLinear()
    .domain([0, 100])
    .range([width/2 + margin.middle, (width+margin.right)]);

    const yPercentage = d3.scaleBand()
    .domain(topics)
    .range([0, height])
    .padding(0.3);

    // Scales
    const color = d3.scaleOrdinal().domain(sentiment_counts).range(["#EE6123", "#D9D9D9", "#00916E"]);

    // TOTALS CHART
    const xAxisTotals = d3.axisBottom(xTotals).ticks(5, '~s').tickSizeOuter(0);
    const yAxisTotals = d3.axisLeft(yTotals);

    svg.append('g')
        .attr('transform', `translate(0,${height-height*0.08})`)
        .call(xAxisTotals)
        .call(g => g.select('.domain').remove())
        .selectAll('text')
        .attr('font-size', 14);

    svg.append("g")
        .call(yAxisTotals)
        .call(g => g.select('.domain').remove())
        .selectAll('text')
        .attr('font-weight', 700) // bold the topics
        .attr('font-size', 14);

    // Draw bars
    const layers = svg.append('g')
        .selectAll('g')
        .data(stackedData)
        .join('g')
        .attr('fill', d => color(d.key));

    layers.each(function(_, i) {
        d3.select(this)
            .selectAll('rect')
            .data(d => d)
            .join('rect')
            .attr('x', d => xTotals(d[0]))
            .attr('y', d => yTotals(d.data.topic))
            .attr('height', yTotals.bandwidth())
            .attr('width', d => xTotals(d[1]) - xTotals(d[0]))
            .attr('font-size', 14);
    });


    // PERCENTAGE CHART
    const xAxisPercentage = d3.axisBottom(xPercentage).ticks(5, '~s').tickSizeOuter(0);
    const yAxisPercentage = d3.axisLeft(yPercentage);

    svg.append('g')
        .attr('transform', `translate(0,${height-height*0.08})`)
        .call(xAxisPercentage)
        .call(g => g.select('.domain').remove())
        .selectAll('text')
        .attr('font-size', 14);

    svg.append("g")
        .call(yAxisPercentage)
        .call(g => g.select('.domain').remove())
        .selectAll('text')
        .attr('font-weight', 700) // bold the topics
        .attr('font-size', 14);

    // Draw bars
    const layers_2 = svg.append('g')
        .selectAll('g')
        .data(stackedData)
        .join('g')
        .attr('fill', d => color(d.key));

    layers_2.each(function(_, i) {
        d3.select(this)
            .selectAll('rect')
            .data(d => d)
            .join('rect')
            .attr('x', d => xPercentage(d[0]))
            .attr('y', d => yPercentage(d.data.topic))
            .attr('height', yPercentage.bandwidth())
            .attr('width', d => xPercentage(d[1]) - xPercentage(d[0]))
            .attr('font-size', 14);
    });






//     // add legend
//     const legendData = [
//         {label: 'Negative', color: '#EE6123'},  // Orange
//         {label: 'Neutral', color: '#D9D9D9'},   // Gray
//         {label: 'Positive', color: '#00916E'}   // Green
//     ];
//     const legend = svg.append('g')
//         .attr('class', 'legend')
//         .attr('transform', `translate(${width*0.9},${height*0.1})`); // Adjust position as needed

//     // add color blocks
//     legend.selectAll('rect')
//         .data(legendData)
//         .enter()
//         .append('rect')
//         .attr('x', 0)
//         .attr('y', (_, i) => i * 20)
//         .attr('width', 10)
//         .attr('height', 10)
//         .attr('fill', d => d.color);

//     // add labels for each color
//     legend.selectAll('text')
//         .data(legendData)
//         .enter()
//         .append('text')
//         .attr('x', 20)
//         .attr('y', (_, i) => i * 20 + 7)
//         .text(d => d.label)
//         .attr('font-size', 14)
//         .attr('alignment-baseline', 'middle');

//     // Add legend title
//     legend.append('text')
//         .attr('x', 0)
//         .attr('y', -10)
//         .text('Sentiment')
//         .attr('font-size', 14)
//         .attr('font-weight', 'bold');



}