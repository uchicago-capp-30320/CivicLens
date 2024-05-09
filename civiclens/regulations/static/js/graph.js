// graph.js

export function drawGraph() {
    // set up
    const margin = { top: 10, right: 100, bottom: 20, left: 150 };

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
    const data = JSON.parse(validJSONString);


    const sentiment_counts = Object.keys(data[0]).filter(d => ((d != "topic") & (d != "source")));
    const topics = data.map(d => d.topic);

    const stackedData = d3.stack().keys(sentiment_counts)(data);

    const xMax = d3.max(stackedData[stackedData.length - 1], d => d[1]);

    // Scales
    const x = d3.scaleLinear().domain([0, xMax]).nice().range([0, width]);
    const y = d3.scaleBand().domain(topics).range([0, height]).padding(0.3);
    const color = d3.scaleOrdinal().domain(sentiment_counts).range(["#EE6123", "#D9D9D9", "#00916E"]);

    // Axes
    const xAxis = d3.axisBottom(x).ticks(5, '~s').tickSizeOuter(0);
    const yAxis = d3.axisLeft(y);

    svg.append('g')
        .attr('transform', `translate(0,${height-height*0.08})`)
        .call(xAxis)
        .call(g => g.select('.domain').remove())
        .selectAll('text')
        .attr('font-size', 14);

    // Add x-axis label
    svg.append('text')
        .attr('x', width / 2)
        .attr('y', height + margin.top*1.5) // Adjust vertical position as needed
        .attr('text-anchor', 'middle')
        .text('Number of Comments') // this needs a bit of work
        .attr('font-size', 12);

    svg.append("g")
        .call(yAxis)
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
            .attr('x', d => x(d[0]))
            .attr('y', d => y(d.data.topic))
            .attr('height', y.bandwidth())
            .attr('width', d => x(d[1]) - x(d[0]))
            .attr('font-size', 14);
    });

    // add legend
    const legendData = [
        {label: 'Negative', color: '#EE6123'},  // Orange
        {label: 'Neutral', color: '#D9D9D9'},   // Gray
        {label: 'Positive', color: '#00916E'}   // Green
    ];
    const legend = svg.append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${width*0.9},${height*0.1})`); // Adjust position as needed

    // add color blocks
    legend.selectAll('rect')
        .data(legendData)
        .enter()
        .append('rect')
        .attr('x', 0)
        .attr('y', (_, i) => i * 20)
        .attr('width', 10)
        .attr('height', 10)
        .attr('fill', d => d.color);

    // add labels for each color
    legend.selectAll('text')
        .data(legendData)
        .enter()
        .append('text')
        .attr('x', 20)
        .attr('y', (_, i) => i * 20 + 7)
        .text(d => d.label)
        .attr('font-size', 14)
        .attr('alignment-baseline', 'middle');

    // Add legend title
    legend.append('text')
        .attr('x', 0)
        .attr('y', -10)
        .text('Sentiment')
        .attr('font-size', 14)
        .attr('font-weight', 'bold');
}