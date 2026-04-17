// This was... mildly annoying

// State Management
let appState = {
    viewMode: 'macro',
    metric: 'total',
    activeChapter: 'A00-B99',
    customCodes: [],
    hiddenEntities: [],
    currentData: [],
    masterChapters: [],
    masterCodes: [],
    entityColors: {},
    customColorscale: [] 
};

// Initialization
document.addEventListener('DOMContentLoaded', async () => {
    await fetchMasterLists();
    switchView('macro'); 
});

async function fetchMasterLists() {
    let resChap = await fetch('/api/chapters');
    appState.masterChapters = await resChap.json();

    let resCodes = await fetch('/api/codes');
    appState.masterCodes = await resCodes.json();
}

// UI Interactions
function setMetric(metricName) {
    appState.metric = metricName;
    
    document.querySelectorAll('.metric-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('onclick').includes(metricName)) {
            btn.classList.add('active');
        }
    });
    renderDashboard(); 
}

function switchView(mode) {
    appState.viewMode = mode;
    appState.hiddenEntities = []; 
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('onclick').includes(mode)) {
            btn.classList.add('active');
        }
    });
    
    renderControls();
    fetchDataAndRender();
}

function renderControls() {
    const controlsDiv = document.getElementById('view-controls');
    controlsDiv.innerHTML = ''; 

    if (appState.viewMode === 'macro') {
        controlsDiv.innerHTML = '<p><em>Use the legend below to filter chapters</em></p>';
    } 
    else if (appState.viewMode === 'chapter') {
        let selectHtml = `<label><strong>Select Chapter:</strong> </label>
                          <select id="chap-dropdown" onchange="appState.activeChapter = this.value; fetchDataAndRender();">`;
        appState.masterChapters.forEach(c => {
            let selected = (c.summary_code === appState.activeChapter) ? 'selected' : '';
            selectHtml += `<option value="${c.summary_code}" ${selected}>${c.summary_code}: ${c.description}</option>`;
        });
        selectHtml += `</select>`;
        controlsDiv.innerHTML = selectHtml;
    } 
    else if (appState.viewMode === 'custom') {
        let searchHtml = `<label><strong>Add Diagnosis:</strong> </label>
                          <input list="codes-list" id="custom-search" placeholder="Search by code or name...">
                          <button onclick="addCustomCode()">Add to Chart</button>
                          <button onclick="appState.customCodes=[]; fetchDataAndRender();" style="background:#e53e3e; color:white; margin-left:10px;">Clear All</button>
                          <datalist id="codes-list">`;
        appState.masterCodes.forEach(c => {
            searchHtml += `<option value="${c.code}">${c.code}: ${c.description}</option>`;
        });
        searchHtml += `</datalist>`;
        controlsDiv.innerHTML = searchHtml;
    }
}

function addCustomCode() {
    const input = document.getElementById('custom-search').value;
    const code = input.substring(0, 3).toUpperCase(); 
    
    if (code && !appState.customCodes.includes(code)) {
        appState.customCodes.push(code);
        document.getElementById('custom-search').value = ''; 
        fetchDataAndRender();
    }
}

async function fetchDataAndRender() {
    let endpoint = '';
    let config = { method: 'GET' };

    if (appState.viewMode === 'macro') {
        endpoint = '/api/admissions/summary';
    } else if (appState.viewMode === 'chapter') {
        endpoint = `/api/admissions/chapter/${appState.activeChapter}`;
    } else if (appState.viewMode === 'custom') {
        if (appState.customCodes.length === 0) {
            appState.currentData = [];
            renderDashboard();
            return;
        }
        endpoint = '/api/admissions/custom';
        config = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codes: appState.customCodes })
        };
    }

    try {
        const response = await fetch(endpoint, config);
        const data = await response.json();
        
        data.forEach(item => {
            if (appState.viewMode === 'macro') {
                item.display_name = `${item.summary_code}: ${item.chapter_name}`;
            } else {
                item.display_name = `${item.diagnosis_code}: ${item.diagnosis_name}`;
            }
        });
        
        appState.currentData = data;

        
        if (appState.viewMode === 'chapter') {
            const entityVolumes = {};
            
            data.forEach(item => {
                if (!entityVolumes[item.display_name]) entityVolumes[item.display_name] = 0;
                entityVolumes[item.display_name] += (item.total + item.emergency + item.planned);
            });

            const sortedEntities = Object.keys(entityVolumes).sort((a, b) => entityVolumes[b] - entityVolumes[a]);

            // Only display the top 12 codes for chapter view
            if (sortedEntities.length > 12) {
                appState.hiddenEntities = sortedEntities.slice(12);
            } else {
                appState.hiddenEntities = [];
            }
        }

        renderDashboard();
    } catch (err) {
        console.error("Fetch Error:", err);
    }
}

function renderDashboard() {
    const uniqueEntities = [...new Set(appState.currentData.map(item => item.display_name))];
    appState.entityColors = {};
    appState.customColorscale = [];
    
    uniqueEntities.forEach((entity, index) => {
        const color = `hsl(${(index * 360 / Math.max(uniqueEntities.length, 1)) % 360}, 75%, 45%)`;
        appState.entityColors[entity] = color;
        
        const norm = uniqueEntities.length > 1 ? index / (uniqueEntities.length - 1) : 0;
        appState.customColorscale.push([norm, color]);
    });
    renderLegend(uniqueEntities);
    renderPlotlyChart(uniqueEntities);
}

function renderLegend(uniqueEntities) {
    const legendDiv = document.getElementById('interactive-legend');
    legendDiv.innerHTML = ''; 

    uniqueEntities.forEach(entity => {
        const pill = document.createElement('div');
        pill.className = 'legend-pill';
        pill.textContent = entity.length > 65 ? entity.substring(0, 65) + '...' : entity;
        
        const isHidden = appState.hiddenEntities.includes(entity);
        
        if (isHidden) {
            pill.classList.add('hidden-pill');
        } else {
            pill.style.backgroundColor = appState.entityColors[entity];
        }

        pill.onclick = () => {
            if (isHidden) {
                appState.hiddenEntities = appState.hiddenEntities.filter(e => e !== entity);
            } else {
                appState.hiddenEntities.push(entity);
            }
            renderPlotlyChart(uniqueEntities); 
            renderLegend(uniqueEntities); 
        };
        legendDiv.appendChild(pill);
    });
}

function renderPlotlyChart(uniqueEntities) {
    const chartDiv = document.getElementById('chart-container');
    const visibleEntities = uniqueEntities.filter(e => !appState.hiddenEntities.includes(e));
    
    if (visibleEntities.length === 0) {
        Plotly.purge(chartDiv);
        chartDiv.innerHTML = '<h3 style="text-align:center; margin-top:100px; color:#718096;">No data selected. Click items in the legend or add codes to view.</h3>';
        return;
    }

    if (chartDiv.innerHTML.includes('<h3')) {
        chartDiv.innerHTML = '';
    }

    const xYears = ['2016-17', '2017-18', '2018-19', '2019-20', '2020-21', '2021-22', '2022-23'];
    const yEntities = [...visibleEntities].reverse(); 
    const zMatrix = [];
    const rawMatrix = []; 

    yEntities.forEach(entity => {
        const entityData = appState.currentData.filter(item => item.display_name === entity);
        
        const getVal = (year) => {
            const record = entityData.find(i => i.financial_year === year);
            return record ? record[appState.metric] : 0; 
        };

        const v16 = getVal('2016-17');
        const v17 = getVal('2017-18');
        const v18 = getVal('2018-19');
        const v19 = getVal('2019-20');
        const v20 = getVal('2020-21');
        const v21 = getVal('2021-22');
        const v22 = getVal('2022-23');

        rawMatrix.push([v16, v17, v18, v19, v20, v21, v22]);
        const rowMax = Math.max(v16, v17, v18, v19, v20, v21, v22);

        zMatrix.push([
            rowMax > 0 ? v16 / rowMax : 0,
            rowMax > 0 ? v17 / rowMax : 0,
            rowMax > 0 ? v18 / rowMax : 0,
            rowMax > 0 ? v19 / rowMax : 0,
            rowMax > 0 ? v20 / rowMax : 0,
            rowMax > 0 ? v21 / rowMax : 0,
            rowMax > 0 ? v22 / rowMax : 0
        ]);
    });

    const trace = {
        type: 'heatmap',
        x: xYears,
        y: yEntities,
        z: zMatrix,
        customdata: rawMatrix,
        colorscale: 'YlOrRd', 
        showscale: false,
        hovertemplate: '<b>%{y}</b><br>Year: %{x}<br>Admissions: %{customdata:,.0f}<extra></extra>' 
    };

    // Configure the Layout
    const layout = {
        margin: { 
            l: 300,
            r: 50, 
            t: 30, 
            b: 50 
        },
        xaxis: { 
            title: 'Financial Year',
            side: 'bottom',
            tickangle: 0
        },
        yaxis: {
            automargin: true,
            tickfont: { size: 11 }
        },
        paper_bgcolor: 'white',
        plot_bgcolor: 'white'
    };

    Plotly.react(chartDiv, [trace], layout, {responsive: true});
}

function enableAllCategories() {
    appState.hiddenEntities = [];
    const uniqueEntities = [...new Set(appState.currentData.map(item => item.display_name))];
    renderPlotlyChart(uniqueEntities);
    renderLegend(uniqueEntities);
}

function disableAllCategories() {
    const uniqueEntities = [...new Set(appState.currentData.map(item => item.display_name))];
    appState.hiddenEntities = [...uniqueEntities]; 
    renderPlotlyChart(uniqueEntities);
    renderLegend(uniqueEntities);
}