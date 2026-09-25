
frappe.pages['monthly-quality-repo'].on_page_load = function(wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: '',
		single_column: true
	});
	$(page.page_head).hide();

	const header_wrapper = $(`
		<div style="text-align: center; margin-bottom: 20px;">
			<h2 id="page-title" style="color: #FFFFFF; margin: 0; border-bottom: 2px solid #FFFFFF; display: inline-block; padding-bottom: 5px;">
				Monthly Quality Report - ${get_month_name(frappe.datetime.get_today().split('-')[1])}
			</h2>
		</div>
	`).prependTo(page.body);

	wrapper = $(wrapper).css({
		"background-color": "#07214D",
		"padding": "20px",
		"color": "white"
	});

	const from_date_filter = page.add_field({
		label: 'From Date',
		fieldtype: 'Date',
		fieldname: 'from_date',
		// default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		change: load_data_from_filters
	});

	const to_date_filter = page.add_field({
		label: 'To Date',
		fieldtype: 'Date',
		fieldname: 'to_date',
		// default: frappe.datetime.get_today(),
		change: load_data_from_filters
	});

	// Create wrapper for report content
	const report_wrapper = $('<div id="report-wrapper"></div>').appendTo(page.body);

	// Filters styling
	$(document).ready(() => {
		$('.page-head, .page-head-space, .page-title').hide();
		$('.page-content').css({
			'padding-top': '10px',
			'background-color': '#0B2245'
		});
		$('.page-main-content').css({
			'margin-top': '0px',
			'padding-top': '0px'
		});
		$('.page-form').css({
			display: 'flex',
			'justify-content': 'flex-end',
			'align-items': 'center',
			'gap': '10px',
			'margin-bottom': '10px',
			'background': 'transparent',
			'border': 'none',
			'box-shadow': 'none'
		});
		$('.frappe-control, .frappe-control input, .control-input-wrapper').css({
			'color': '#fff',
			'border': '1px solid #ccc'
		});
		$('.frappe-control').css({
			'margin': '0',
			'padding': '0 8px',
			'background': 'transparent',
			'box-shadow': 'none',
			'border': 'none',
			'min-width': '120px'
		});
		$('.frappe-control select').css({
			'background': '#0B2245',
			'border': '1px solid #ccc',
			'color': '#fff',
			'width': '100%',
			'padding': '4px 8px',
			'border-radius': '4px'
		});
		page.fields_dict.from_date.$wrapper.find('input').css({
			backgroundColor: '#007BFF',
			color: 'white'
		});
		page.fields_dict.to_date.$wrapper.find('input').css({
			backgroundColor: '#007BFF',
			color: 'white'
		});
	});

	function get_month_name(month) {
		const month_names = {
			'01': 'January', '02': 'February', '03': 'March', '04': 'April',
			'05': 'May', '06': 'June', '07': 'July', '08': 'August',
			'09': 'September', '10': 'October', '11': 'November', '12': 'December'
		};
		return month_names[month] || '';
	}

	function load_data(from_date, to_date) {
		frappe.call({
			method: "taihan.taihan.page.monthly_quality_repo.monthly_quality_report.get_monthly_quality_data",
			args: { from_date, to_date },
			callback(r) {
				if (r.message) {
					frappe.require("https://cdn.jsdelivr.net/npm/chart.js", () => {
						render_report(r.message);
					});
				}
			}
		});
	}

	function load_data_from_filters() {
		const from_date = page.fields_dict.from_date.get_value();
		const to_date = page.fields_dict.to_date.get_value();
		if (from_date && to_date) {
			$("#page-title").text(`Monthly Quality Report - ${get_month_name(from_date.split('-')[1])}`);
			load_data(from_date, to_date);
		}
	}

	function render_report(data) {
		const container = $('#report-wrapper');
		container.empty(); // ✅ Clear previous report only

		const section = $(`<div class="report-section"></div>`).appendTo(container);

		// === FPY Table & Chart ===
		const fpy_row = $(`<div style="display: flex; gap: 20px; justify-content: space-between;"></div>`).appendTo(section);
        
		const table_html = `
			<div style="flex: 1;">
            <br><br>
				<table style="width: 100%; border-collapse: collapse; background-color: #1D3D6E; color: white; font-size: 13px;" border="1">
					<tr>
						<th colspan="6" style="text-align: center; padding: 8px; font-size: 15px; color: #98F600;">
							First Attempt Pass Yield (FPY)
						</th>
					</tr>
					<tr>
						<th style="text-align:center">Stage</th>
						<th style="text-align:center">Total Output (KM)</th>
						<th style="text-align:center">Observation (KM)</th>
						<th style="text-align:center">Hold (KM)</th>
						<th style="text-align:center">Released OK (KM)</th>
						<th style="text-align:center">PASS Rate in %</th>
					</tr>
					${
                    data.fpy_table.length > 0
                        ? data.fpy_table.map(row => `
                            <tr>
                                <td>${row.operation}</td>
                                <td style="text-align:right">${row.total_output}</td>
                                <td style="text-align:right">${row.observation || '-'}</td>
                                <td style="text-align:right">${row.hold || '-'}</td>
                                <td style="text-align:right">${row.released_ok}</td>
                                <td style="text-align:right">${row.pass_rate}</td>
                            </tr>
                        `).join('')
                        : `<tr><td colspan="6" style="text-align:center; padding:10px;">No Data Found</td></tr>`
                }

				</table>
			</div>
		`;
		fpy_row.append(table_html);

		const chart_wrapper = $(`<div style="flex: 1;"><canvas id="fpy_chart" height="250"></canvas></div>`);
		fpy_row.append(chart_wrapper);

		new Chart(chart_wrapper.find('canvas')[0], {
			type: 'bar',
			data: {
				labels: data.fpy_table.map(x => x.operation),
				datasets: [
					{ label: 'Total Output (KM)', data: data.fpy_table.map(x => x.total_output), backgroundColor: '#0073e6' },
					{ label: 'Observation (KM)', data: data.fpy_table.map(x => x.observation || 0), backgroundColor: '#f1c40f' },
					{ label: 'Hold (KM)', data: data.fpy_table.map(x => x.hold || 0), backgroundColor: '#e74c3c' },
					{ label: 'Released OK (KM)', data: data.fpy_table.map(x => x.released_ok), backgroundColor: '#00ff00' },
					{ label: 'PASS Rate in %', data: data.fpy_table.map(x => x.pass_rate), backgroundColor: '#ffd700' }
				]
			},
			options: {
				responsive: true,
				plugins: {
					legend: { labels: { color: 'white' } },
					title: { display: true, text: 'First Attempt Pass Yield (FPY)', color: 'white', font: { size: 16 } }
				},
				scales: {
					x: { ticks: { color: 'white' }, grid: { color: '#444' } },
					y: { beginAtZero: true, ticks: { color: 'white' }, grid: { color: '#444' } }
				}
			}
		});

		// === PY Table & Chart ===
		const py_row = $(`<div style="display: flex; gap: 20px; justify-content: space-between;"></div>`).appendTo(section);
		const py_table_html = `
			<div style="flex: 1;">
            <br> <br> <br>
				<table style="width: 50%; border-collapse: collapse; background-color: #1D3D6E; color: white;" border="1">
					<tr>
						<th colspan="2" style="text-align: center; padding: 8px; font-size: 15px; color: #FF7F50;">
							Pass Yield (PY)
						</th>
					</tr>
					<tr>
						<th style="text-align:center">Stage</th>
						<th style="text-align:center">Total Output (KMs)</th>
					</tr>
					${
                        data.fpy_table.length > 0
                            ? data.fpy_table.map(row => `
                                <tr>
                                    <td>${row.operation}</td>
                                    <td style="text-align:right">${row.total_output}</td>
                                </tr>
                            `).join('')
                            : `<tr><td colspan="2" style="text-align:center; padding:10px;">No Data Found</td></tr>`
                    }

				</table>
			</div>
		`;
		py_row.append(py_table_html);

		const py_chart_wrapper = $(`<div style="flex: 1;"><canvas id="py_chart" height="200"></canvas></div>`);
		py_row.append(py_chart_wrapper);

		new Chart(py_chart_wrapper.find('canvas')[0], {
			type: 'bar',
			data: {
				labels: data.fpy_table.map(x => x.operation),
				datasets: [{ label: 'Pass Yield (KM)', data: data.fpy_table.map(x => x.total_output), backgroundColor: '#00FF00' }]
			},
			options: {
				indexAxis: 'y',
				plugins: { legend: { labels: { color: 'white' } } },
				scales: {
					x: { ticks: { color: 'white' }, grid: { color: '#444' } },
					y: { ticks: { color: 'white' }, grid: { color: '#444' } }
				}
			}
		});

		// === Output CKM Chart ===
        const from_date = page.fields_dict.from_date.get_value();
		const to_date = page.fields_dict.to_date.get_value();
		frappe.call({
    method: "taihan.taihan.page.monthly_quality_repo.monthly_quality_report.get_output_ckm_by_month",
    args:{from_date,to_date},
    callback(res) {
        if (res.message) {
            render_output_ckm_history(res.message);
        }
    }
});
function render_output_ckm_history(data) {
    const ckm_data = data.history || [];
    const avg_ckm = data.average_ckm || 0;

    const container = $('#report-wrapper');

    const history_row = $(`
        <div style="display: flex; justify-content: space-between; gap: 30px; margin-top: 40px;">
            <div style="flex: 1;"><br>
                <table style="width: 60%; border-collapse: collapse; background-color: #1D3D6E; color: white;" border="1">
                    
                    <tr>
                        <th style="text-align:center">Month</th>
                        <th style="text-align:center">Output CKM</th>
                    </tr>
                    ${
                        ckm_data.length > 0
                            ? ckm_data.map(row => `
                                <tr>
                                    <td style="text-align:center">${row.label}</td>
                                    <td style="text-align:right">${row.value}</td>
                                </tr>
                            `).join('')
                            : `<tr><td colspan="2" style="text-align:center; padding:10px;">No Data Found</td></tr>`
                    }

                </table>
                <h4 style="color:white;text-align:left;margin-top:20px;">Monthly Average CKM: 
        <span style="background:white;color:black;border-radius:5px;">${avg_ckm}</span>
    </h4>
            </div>
            <div style="flex: 1;">
                <canvas id="ckm_history_chart" height="250"></canvas>
            </div>
        </div>
    `);

    container.append(history_row);
    // container.append(`<h4 style="color:white;text-align:center;margin-top:20px;">Monthly Average CKM: 
    //     <span style="background:white;color:black;padding:4px 10px;border-radius:5px;">${avg_ckm}</span>
    // </h4>`);
    new Chart(document.getElementById('ckm_history_chart'), {
        type: 'line',
        data: {
            labels: ckm_data.map(x => x.label),
            datasets: [{
                label: 'Output CKM',
                data: ckm_data.map(x => x.value),
                borderColor: '#00FFFF',
                backgroundColor: 'rgba(0,255,255,0.3)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#FFFFFF'
            }]
        },
        options: {
            plugins: { legend: { labels: { color: 'white' } } },
            scales: {
                x: { ticks: { color: 'white' }, grid: { color: '#444' } },
                y: { ticks: { color: 'white' }, grid: { color: '#444' } }
            }
        }
    });

   
}



	}

	// Initial load
	load_data(
		page.fields_dict.from_date.get_value(),
		page.fields_dict.to_date.get_value()
	);
};
