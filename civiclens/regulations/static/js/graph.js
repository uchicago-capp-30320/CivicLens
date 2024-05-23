function getIndices(length) {
    if (length < 0) {
        throw new Error("Length must be a non-negative integer");
    }
    return Array.from({ length }, (_, index) => index);
}

const drawOneHorizonalStackedBarGraph = function(){
    // Clear existing content in the chart div
    if (!document.getElementById("chart")) {
        console.log("Chart element not found.");
        return; // Exit if chart element doesn't exist
    }

    // Clear only the SVG element from the chart div
    d3.select('#chart').select('svg').remove();

    // set up
    const margin = { top: 10, right: 150, bottom: 20, left: 150 };
    const width = document.getElementById("chart").clientWidth - margin.left - margin.right;
    const height = document.getElementById("chart").clientHeight - margin.top - margin.bottom;
    const legend_width = document.getElementById("chart").clientWidth - margin.left - (margin.right/2);
    const legend_height = document.getElementById("chart").clientHeight - margin.top - margin.bottom;

    const svg = d3.select('#chart')
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // add legend
    const legendData = [
        {label: 'Negative', color: '#EE6123'},  // Orange
        {label: 'Neutral', color: '#D9D9D9'},   // Gray
        {label: 'Positive', color: '#00916E'}   // Green
    ];

    const legend = svg
        .append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${legend_width*0.9},${legend_height*0.1})`); // Adjust position as needed

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

    // Data
    const stringData = document.getElementById('topics').innerHTML;
    const validJSONString = stringData.replace(/'/g, '"');
    // get only first 5 elements
    const raw_data = JSON.parse(validJSONString).slice(0, 5);

    const existing_topics = [];
    const data = raw_data.map(d => {
        console.log(d);
        let ret = {}

        // use a topic name that hasn't been used before
        for (let i = 0; i < d.topic.length; i++) {
            const topic = d.topic[i];
            console.log(existing_topics);
            if (!existing_topics.includes(topic)) {
                ret.topic = topic;
                existing_topics.push(topic);
                break;
            }
        }

        if (d.negative){
            ret.negative = d.negative
        }
        if (d.negative){
            ret.negative = d.negative
        }
        if (d.neutral){
            ret.neutral = d.neutral
        }
        if (d.positive){
            ret.positive = d.positive
        }
        return ret
    });

    const sentiment_counts = ["negative", "neutral", "positive"];
    const topics = data.map(d => d.topic);
    const topics_index = getIndices(topics.length);
    const xMax = d3.max(raw_data.map(d => d.total).flat());
    const stackedData = d3.stack().keys(sentiment_counts)(data);

    // Scales
    const x = d3.scaleLinear().domain([0, xMax]).range([0, width]);
    const y = d3.scaleBand().domain(topics_index).range([0, height]).padding(0.3);
    const color = d3.scaleOrdinal().domain(["negative","neutral","positive"]).range(["#EE6123", "#D9D9D9", "#00916E"]);

    // Axes
    const xAxis = d3.axisBottom(x).ticks(5, '~s').tickSizeOuter(0);
    const yAxis = d3.axisLeft(y);

    svg.append('g')
        .attr('transform', `translate(0,${height-height*0.08})`)
        .call(xAxis)
        .call(g => g.select('.domain').remove())
        .selectAll('text')
        .attr('font-size', 14);

    svg.append("g")
        .call(yAxis)
        // .attr('transform', `translate(0,${-y.bandwidth()/2})`)
        .call(g => g.select('.domain').remove())
        .selectAll('text')
        .data(data)
        .attr('font-weight', 700) // bold the topics
        .attr('text-align', 'center')
        .text(d => d.topic)
        // .title((d,i) => raw_data[i].topic)
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
            .attr('y', (d, i) => y(i))
            .attr('height', y.bandwidth())
            .attr('width', d => x(d[1]) - x(d[0]))
            .attr('font-size', 14);
    });

}()
;
