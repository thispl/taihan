// Copyright (c) 2025, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on("In Process Testing Dashboard", {
    // refresh(frm) {
    //     console.log(frm.doc.report)
    // },
    download(frm) {
        if (frm.doc.report == 'Currency Exchange Gain / Loss') {
                console.log("outside")
                var path = 'taihan.taihan.doctype.in_process_testing_dashboard.profit_loss_report.download'
                if (path) {
                    window.location.href = repl(frappe.request.url +
                        '?cmd=%(cmd)s&%(args)s', {
                        cmd: path,
                    });
            }
            
        }
        else if(frm.doc.report=="In Process Testing Report" && !frm.doc.date || !frm.doc.to_date){
            frappe.msgprint("Kindly enter the From date and To date")
        }
        else if(frm.doc.report=="In Process Testing Report" && frm.doc.date && frm.doc.to_date){
            frappe.call({
                method: "taihan.taihan.doctype.in_process_testing_dashboard.inprocess_report.download_excel",
                args: {
                    date:frm.doc.date,
                    to_date:frm.doc.to_date
                    
                },
                callback: function (r) {
                    if (r.message) {
                        let blob = new Blob([new Uint8Array(r.message.content)], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
                        let link = document.createElement("a");
                        link.href = window.URL.createObjectURL(blob);
                        link.download = r.message.filename;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                    }
                }
            });
        }
        else if (frm.doc.report == 'Delivery Details Report') {
                console.log("outside")
                var path = 'taihan.taihan.doctype.in_process_testing_dashboard.profit_loss_report.export_delivery_report'
                if (path) {
                    window.location.href = repl(frappe.request.url +
                        '?cmd=%(cmd)s&%(args)s', {
                        cmd: path,
                    });
            }
            
        }
    }
});
