# Copyright (c) 2022, Abdulla and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
from frappe.utils.file_manager import get_file
from datetime import date, timedelta, datetime
import openpyxl
from openpyxl import Workbook
import openpyxl
import xlrd
from frappe.utils import cstr, add_days, date_diff, getdate, format_date
import re
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import GradientFill, PatternFill
from six import BytesIO, string_types
from frappe.utils import (
    flt,
    cint,
    cstr,
    get_html_format,
    get_url_to_form,
    gzip_decompress,
    format_duration,
)

class ProductSearch(Document):
    @frappe.whitelist()
    def get_data(self):
        data = '<table class="table table-bordered" style="width:70%">'
        data += '<tr><th colspan="12" style="padding:1px;border:1px solid black;background-color:#009ACD;color:white;"><center>Production Details</center></th></tr>'
        job_card = frappe.get_all("Job Card",{"docstatus":("!=",2),"production_item":self.item_code},["*"])
        
        if job_card:
            data += '''
            <tr>
                <td colspan="2" style="padding:1px;border:1px solid black;color:white;background-color:#009ACD;"><center><b>Employee</b></center></td>
                <td colspan="2" style="padding:1px;border:1px solid black;color:white;background-color:#009ACD;"><center><b>From Time</b></center></td>
                <td colspan="2" style="padding:1px;border:1px solid black;color:white;background-color:#009ACD;"><center><b>To Time</b></center></td>
                <td colspan="2" style="padding:1px;border:1px solid black;color:white;background-color:#009ACD;"><center><b>Machine</b></center></td>
                <td colspan="2" style="padding:1px;border:1px solid black;color:white;background-color:#009ACD;"><center><b>QC Status</b></center></td>
            </tr>
            '''
            for j in job_card:
                job_doc = frappe.get_doc("Job Card",j.name)
                qc_status = frappe.db.get_value ("Quality Inspection",{"name":job_doc.quality_inspection},["status"])
                for i in job_doc.time_logs:
                    data += f'''
                    <tr>
                        <td colspan="2" style="padding:1px;border:1px solid black;"><center><b>{i.employee}</b></center></td>
                        <td colspan="2" style="padding:1px;border:1px solid black;"><center><b>{i.from_time}</b></center></td>
                        <td colspan="2" style="padding:1px;border:1px solid black;"><center><b>{i.to_time}</b></center></td>
                        <td colspan="2" style="padding:1px;border:1px solid black;"><center><b>{job_doc.custom_machine_no or ''}</b></center></td>
                        <td colspan="2" style="padding:1px;border:1px solid black;"><center><b>{qc_status or ''}</b></center></td>
                    </tr>
                    '''
        else:
            data += '<tr><td align="center" colspan="10" style="padding:1px;border:1px solid black;background-color:#fe3f0c;color:white;"><b>No Production Available</b></td></tr>'
        data += '</table>'

        return data
    
    @frappe.whitelist()
    def get_pod(self):
        maintain_stock = frappe.db.get_value("Item",{"name":self.item_code},["is_stock_item"])
        if maintain_stock==1:	
            item = frappe.get_value('Item',{'item_code':self.item_code},'item_code')
            new_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty,sum(`tabPurchase Order Item`.received_qty) as d_qty from `tabPurchase Order`
            left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
            where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus = 1  and `tabPurchase Order`.status != 'Closed' order by `tabPurchase Order Item`.schedule_date""" % (item), as_dict=True)[0]
            if not new_po['qty']:
                new_po['qty'] = 0
            if not new_po['d_qty']:
                new_po['d_qty'] = 0
            ppoc_total = new_po['qty'] - new_po['d_qty']
            if ppoc_total == 0.0 :
                frappe.msgprint("No Pending Purchase Receipt")
                data = ''
            else:
                data = ''
                data += '<table class="table table-bordered" style="width:75%"><tr><td style="padding:1px;border: 1px solid black;background-color:#4149b5; color: white; width:75%" colspan=3><center>Pending PO Details</center></td></tr>'
                data += '<tr><td style="padding:1px;width:25%;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: center"><b>Purchase Order</b></td><td style="padding:1px;width:25%;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: center"><b>Expected Date of Arrival</b></td><td style="padding:1px;width:25%;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: center"><b>Pending Qty</b></td></tr>'
                sa = frappe.db.sql(""" select parent,qty,schedule_date,received_qty,rate from `tabPurchase Order Item` where `tabPurchase Order Item`.item_code = '%s' order by `tabPurchase Order Item`.schedule_date """ %(item),as_dict=True)
                for i in sa:
                    if i.qty == i.received_qty:
                        pass
                    else:
                        sb = frappe.get_doc("Purchase Order", i.parent)
                        if sb.docstatus == 1 and sb.status!= "Closed":
                            pending_qty = i.qty - i.received_qty
                            data += '<tr><td style="border: 1px solid black;text-align: center"><b>%s</b></td><td style="border: 1px solid black;text-align: center"><b>%s</b></td><td style="border: 1px solid black;text-align: center"><b>%s</b></td></tr>' %(i.parent,format_date(i.schedule_date),"{:.2f}".format(pending_qty))

                print(data)
            data += '</table>'
            return data
        else:
            bundle_item = frappe.get_doc("Product Bundle",self.item_code)
            for i in bundle_item.items:
                new_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty,sum(`tabPurchase Order Item`.received_qty) as d_qty from `tabPurchase Order`
                left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
                where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus = 1  and `tabPurchase Order`.status != 'Closed' order by `tabPurchase Order Item`.schedule_date""" % (i.item_code), as_dict=True)[0]
                if not new_po['qty']:
                    new_po['qty'] = 0
                if not new_po['d_qty']:
                    new_po['d_qty'] = 0
                ppoc_total = new_po['qty'] - new_po['d_qty']
                if ppoc_total == 0.0 :
                    frappe.msgprint("No Pending Purchase Receipt")
                    data = ''
                else:
                    data = ''
                    data += '<table class="table table-bordered" style="width:75%"><tr><td style="padding:1px;border: 1px solid black;background-color:#4149b5; color: white; width:75%" colspan=3><center>Pending PO Details</center></td></tr>'
                    data += '<tr><td style="padding:1px;width:25%;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: center"><b>Purchase Order</b></td><td style="padding:1px;width:25%;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: center"><b>Expected Date of Arrival</b></td><td style="padding:1px;width:25%;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: center"><b>Pending Qty</b></td></tr>'
                    sa = frappe.db.sql(""" select parent,qty,schedule_date,received_qty,rate from `tabPurchase Order Item` where `tabPurchase Order Item`.item_code = '%s' order by `tabPurchase Order Item`.schedule_date """ %(i.item_code),as_dict=True)
                    for i in sa:
                        if i.qty == i.received_qty:
                            pass
                        else:
                            sb = frappe.get_doc("Purchase Order", i.parent)
                            if sb.docstatus == 1 and sb.status!= "Closed":
                                pending_qty = i.qty - i.received_qty
                                data += '<tr><td style="border: 1px solid black;text-align: center"><b>%s</b></td><td style="border: 1px solid black;text-align: center"><b>%s</b></td><td style="border: 1px solid black;text-align: center"><b>%s</b></td></tr>' %(i.parent,format_date(i.schedule_date),"{:.2f}".format(pending_qty))

                    print(data)
                data += '</table>'
                return data


    @frappe.whitelist()
    def get_data_perm(self):
        maintain_stock = frappe.db.get_value("Item",{"name":self.item_code},["is_stock_item"])
        if maintain_stock==1:
            company = frappe.db.get_value("Employee",{'user_id':frappe.session.user},'company')
            w_house = frappe.db.get_value("Warehouse",{'company':company,'default_for_stock_transfer':1},['name'])
            item = frappe.get_value('Item',{'item_code':self.item_code},'item_code')
            group = frappe.get_value('Item',{'item_code':self.item_code},'item_group')
            uom = frappe.get_value('Item',{'item_code':self.item_code},'stock_uom')
            # valuation = frappe.get_value('Item',{'item_code':self.item_code},'valuation_rate')
            des = frappe.get_value('Item',{'item_code':self.item_code},'description')
            csp = 'Current Selling Price'
            c_s_p = frappe.get_value('Item Price',{'item_code':self.item_code,'price_list':'Standard Selling'},'price_list_rate') or 0
            cpp = 'Current Purchase Price'
            cost = 'COST'
            pso = 'Pending Sales order'
            po ='Total Purchase Order'
            ppo = 'Pending Purchase order'
            cspp_rate = 0
            cppp_rate = 0
            del_total = 0
            psoc = 0
            ppoc = 0
            ppoc_total = 0
            total_qty=0
            total_res=0
            data = ''
            pos = frappe.db.sql("""select `tabPurchase Order Item`.item_code as item_code,`tabPurchase Order Item`.item_name as item_name,`tabPurchase Order`.supplier as supplier,`tabPurchase Order Item`.qty as qty,`tabPurchase Order Item`.rate as rate,`tabPurchase Order`.transaction_date as date,`tabPurchase Order`.name as po from `tabPurchase Order`
            left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
            where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 """ % (self.item_code), as_dict=True)
            new_so = frappe.db.sql("""select sum(`tabSales Order Item`.qty) as qty,sum(`tabSales Order Item`.delivered_qty) as d_qty from `tabSales Order`
            left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent
            where `tabSales Order Item`.item_code = '%s' and `tabSales Order`.docstatus = 1 and `tabSales Order`.status != 'Closed' """ % (item), as_dict=True)[0]
            if not new_so['qty']:
                new_so['qty'] = 0
            if not new_so['d_qty']:
                new_so['d_qty'] = 0
            del_total = new_so['qty'] - new_so['d_qty']		
                    
            new_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty,sum(`tabPurchase Order Item`.received_qty) as d_qty from `tabPurchase Order`
            left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
            where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus = 1 and `tabPurchase Order`.status != 'Closed' """ % (item), as_dict=True)[0]
            if not new_po['qty']:
                new_po['qty'] = 0
            if not new_po['d_qty']:
                new_po['d_qty'] = 0
            ppoc_total = new_po['qty'] - new_po['d_qty']	
            data += '<table class="table table-bordered" style="width:75%"><tr><th style="padding:1px;border: 1px solid black;background-color:#4149b5; color: white;" colspan=12><center>PRODUCT SEARCH</center></th></tr>'
            data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;color:white;background-color:#6f6f6f;text-align: left"><b>Item Code</b></td><td colspan = 11 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(item)
            # data += '<tr><td colspan = 2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Item Name</b></td><td colspan = 3 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(frappe.db.get_value('Item',item,'item_name'))
            data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Description</b></td><td colspan = 11 style="padding:1px;border: 1px solid black;text-align: left" nowrap><b>%s</b></td></tr>'%(des)
            data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;text-align: left;background-color:#6f6f6f;color:white"><b>%s</b></td><td colspan = 11 style="padding:1px;border: 1px solid black;text-align: left;background-color:#FFFFFF;color:solid black"><b>%s</b></td></tr>'%(csp,f"{c_s_p:.2f}")
            data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Item Group</b></td><td colspan = 11 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(group)
            
            data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;color:white;background-color:#6f6f6f;text-align: left"><b>%s</b></td><td colspan = 11 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(pso,(del_total))
            if ppoc_total != 0.0:
                data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;color:white;background-color:#6f6f6f;text-align: left"><b>%s</b></td><td colspan = 11 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(ppo,(ppoc_total))
            else:
                data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;color:white;background-color:#6f6f6f;text-align: left"><b>%s</b></td><td colspan = 11 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(ppo,(ppoc_total)) 
            
            if not frappe.session.user == "anoop@marazeemqatar.com":
                data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Company</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>QTY</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Res.qty</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>UOM</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>COST</b></center></td></tr>'
            
            if frappe.session.user == "anoop@marazeemqatar.com":
            
                if frappe.session.user == "anoop@marazeemqatar.com" and group == "Eyenor" or group == "NVS" or group == "Secnor":
                    data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Company</b></center></td>td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>QTY</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Res.qty</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>UOM</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>COST</b></center></td></tr>'
                else:
                    data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Company</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>QTY</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Res.qty</b></center></td><td colspan = 2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>UOM</b></center></td></tr>'
            stocks = frappe.get_all(
                "Bin",
                filters={
                    "item_code": item,
                    "warehouse": ("not like", "%Work In Progress%"),
                },
                fields=["actual_qty", "warehouse", "stock_uom", "stock_value", "reserved_qty", "valuation_rate"]
            )

            warehouse_data = {}
            i = 0
            cou = 0
            reser =0
            tot = 'Total'
            if group=='OptiNor':
                uom='Meter'
            # else:
            # 	uom = 'Nos'
            for stock in stocks:
                if stock.warehouse == w_house:
                    frappe.errprint(stock.warehouse)
                    
                    comp = frappe.get_value("Warehouse", stock.warehouse, 'company')
                    valuation = frappe.db.get_value("Bin",{"item_code": item,"warehouse": ("not like", "%Work In Progress%")},["valuation_rate"])
                    entries = frappe.db.get_all("Stock Reservation Entry", 
                                                filters={"item_code": item, "warehouse": stock.warehouse,"status":("Not In",("Cancelled","Delivered")),"docstatus":("!=",2)}, 
                                                fields=["reserved_qty"])
                    total_reserved_qty = sum(flt(entry["reserved_qty"]) for entry in entries)
                    available_qty = stock.actual_qty
                    if comp in warehouse_data:
                        warehouse_data[comp]['available_qty'] += available_qty
                        warehouse_data[comp]['ppoc_total'] += total_reserved_qty
                        warehouse_data[comp]['del_total'] += del_total
                        warehouse_data[comp]['valuation'] =valuation
                    else:
                        warehouse_data[comp] = {
                            'available_qty': available_qty,
                            'ppoc_total': total_reserved_qty,
                            'del_total': del_total,
                            'valuation':valuation
                        }
            for comp, values in warehouse_data.items():
                valuation = values['valuation']
                if not frappe.session.user == "anoop@marazeemqatar.com":
                    if group=='OptiNor':
                        data += '''
                            <tr>
                                <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1 nowrap>{}</td>
                                <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                                <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                                <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>Meter</td>
                                <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:right" colspan=1>{}</td>
                            </tr>
                        '''.format(comp, round(values['available_qty'],2)-(values['ppoc_total']), (values['ppoc_total']), "{:.2f}".format(valuation))	
                
            i = 0
            for stock in stocks:
                if stock.warehouse != w_house:
                    frappe.errprint(stock.warehouse)
                    
                    comp = frappe.get_value("Warehouse", stock.warehouse, 'company')
                    valuation = frappe.db.get_value("Bin",{"item_code": item,"warehouse": ("not like", "%Work In Progress%")},["valuation_rate"])
                    entries = frappe.db.get_all("Stock Reservation Entry", 
                                                filters={"item_code": item, "warehouse": stock.warehouse,"status":("Not In",("Cancelled","Delivered")),"docstatus":("!=",2)}, 
                                                fields=["reserved_qty"])
                    total_reserved_qty = sum(flt(entry["reserved_qty"]) for entry in entries)
                    available_qty = stock.actual_qty
                    if comp in warehouse_data:
                        warehouse_data[comp]['available_qty'] += available_qty
                        warehouse_data[comp]['ppoc_total'] += total_reserved_qty
                        warehouse_data[comp]['del_total'] += del_total
                        warehouse_data[comp]['valuation'] = valuation
                    else:
                        warehouse_data[comp] = {
                            'available_qty': available_qty,
                            'ppoc_total': total_reserved_qty,
                            'del_total': del_total,
                            'valuation':valuation
                        }
            for comp, values in warehouse_data.items():
                valuation=values['valuation']
                if not frappe.session.user == "anoop@marazeemqatar.com":
                    if group=='OptiNor':
                        data += '''
                            <tr>
                                <td style="padding:1px;border: 1px solid black;color:black;font-weight:bold" colspan=1 nowrap>{}</td>
                                <td style="padding:1px;border: 1px solid black;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                                <td style="padding:1px;border: 1px solid black;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                                <td style="padding:1px;border: 1px solid black;color:black;font-weight:bold;text-align:center" colspan=1>Meter</td>
                                <td style="padding:1px;border: 1px solid black;color:black;font-weight:bold;text-align:right" colspan=1>{}</td>
                            </tr>
                        '''.format(comp, round(values['available_qty'],2)-(values['ppoc_total']), (values['ppoc_total']), "{:.2f}".format(valuation))	
                    else:
                        data += '''
                            <tr>
                                <td style="padding:1px;border: 1px solid black;color:black;font-weight:bold" colspan=1 nowrap>{}</td>
                                <td style="padding:1px;border: 1px solid black;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                                <td style="padding:1px;border: 1px solid black;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                                <td style="padding:1px;border: 1px solid black;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                                <td style="padding:1px;border: 1px solid black;color:black;font-weight:bold;text-align:right" colspan=1>{}</td>
                            </tr>
                        '''.format(comp, round(values['available_qty'],2)-(values['ppoc_total']), (values['ppoc_total']),uom,"{:.2f}".format(valuation))	
            for stock in stocks:
                
                if stock.warehouse == w_house:
                    comp = frappe.get_value("Warehouse", stock.warehouse, 'company')
                    entries = frappe.db.get_all("Stock Reservation Entry", 
                                                filters={"item_code": item, "warehouse": stock.warehouse,"status":("Not In",("Cancelled","Delivered")),"docstatus":("!=",2)}, 
                                                fields=["reserved_qty"])
                    total_reserved_qty = sum(flt(entry["reserved_qty"]) for entry in entries)
                    if frappe.session.user == "rifdy@electraqatar.com":
                        available_qty = stock.actual_qty
                    else:
                        available_qty = stock.actual_qty - total_reserved_qty
                    total_res
                    if comp in warehouse_data:
                        warehouse_data[comp]['available_qty'] = available_qty
                        warehouse_data[comp]['ppoc_total'] = total_reserved_qty
                        warehouse_data[comp]['del_total'] = del_total
                    else:
                        warehouse_data[comp] = {
                            'available_qty': available_qty,
                            'ppoc_total': total_reserved_qty,
                            'del_total': del_total
                        }
            for comp, values in warehouse_data.items():
                total_qty +=values['available_qty']
                total_res +=values['ppoc_total']
            if not frappe.session.user == "anoop@marazeemqatar.com":
                data += '''
                    <tr>
                        <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                        <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                        <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                        <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                        <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:right" colspan=1>{}</td>
                    </tr>
                '''.format("Total",round(total_qty,2)-(total_res),(total_res),uom,"-")

            if frappe.session.user == "anoop@marazeemqatar.com":
                if group=='OptiNor':
                    data += '''
                        <tr>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:right" colspan=1>{}</td>
                        </tr>
                    '''.format("Total",round(total_qty,2)-(total_res),(total_res),uom,"-")	

                elif frappe.session.user == "anoop@marazeemqatar.com" and group == "Eyenor" or group == "NVS" or group == "Secnor":
                    data += '''
                        <tr>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                        </tr>
                    '''.format("Total",round(total_qty,2)-(total_res),(total_res),uom,"-")	

                
                else:
                    data += '''
                        <tr>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                        </tr>
                    '''.format("Total",round(total_qty,2)-(total_res),(total_res),uom,"-")	
            
            data += '</table>'

            return data
        else:
            company = frappe.db.get_value("Employee",{'user_id':frappe.session.user},'company')
            w_house = frappe.db.get_value("Warehouse",{'company':company,'default_for_stock_transfer':1},['name'])
            item = frappe.get_value('Item',{'item_code':self.item_code},'item_code')
            group = frappe.get_value('Item',{'item_code':self.item_code},'item_group')
            uom = frappe.get_value('Item',{'item_code':self.item_code},'stock_uom')
            # valuation = frappe.get_value('Item',{'item_code':self.item_code},'valuation_rate')
            des = frappe.get_value('Item',{'item_code':self.item_code},'description')
            csp = 'Current Selling Price'
            c_s_p = frappe.get_value('Item Price',{'item_code':self.item_code,'price_list':'Standard Selling'},'price_list_rate') or 0
            cpp = 'Current Purchase Price'
            cost = 'COST'
            pso = 'Pending Sales order'
            po ='Total Purchase Order'
            ppo = 'Pending Purchase order'
            cspp_rate = 0
            cppp_rate = 0
            del_total = 0
            psoc = 0
            ppoc = 0
            ppoc_total = 0
            total_qty=0
            total_res=0
            data = ''
            pos = frappe.db.sql("""select `tabPurchase Order Item`.item_code as item_code,`tabPurchase Order Item`.item_name as item_name,`tabPurchase Order`.supplier as supplier,`tabPurchase Order Item`.qty as qty,`tabPurchase Order Item`.rate as rate,`tabPurchase Order`.transaction_date as date,`tabPurchase Order`.name as po from `tabPurchase Order`
            left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
            where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 """ % (self.item_code), as_dict=True)
            new_so = frappe.db.sql("""select sum(`tabSales Order Item`.qty) as qty,sum(`tabSales Order Item`.delivered_qty) as d_qty from `tabSales Order`
            left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent
            where `tabSales Order Item`.item_code = '%s' and `tabSales Order`.docstatus = 1 and `tabSales Order`.status != 'Closed' """ % (item), as_dict=True)[0]
            if not new_so['qty']:
                new_so['qty'] = 0
            if not new_so['d_qty']:
                new_so['d_qty'] = 0
            del_total = new_so['qty'] - new_so['d_qty']		
                    
            new_po = frappe.db.sql("""select sum(`tabPurchase Order Item`.qty) as qty,sum(`tabPurchase Order Item`.received_qty) as d_qty from `tabPurchase Order`
            left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
            where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus = 1 and `tabPurchase Order`.status != 'Closed' """ % (item), as_dict=True)[0]
            if not new_po['qty']:
                new_po['qty'] = 0
            if not new_po['d_qty']:
                new_po['d_qty'] = 0
            ppoc_total = new_po['qty'] - new_po['d_qty']	
            data += '<table class="table table-bordered" style="width:75%"><tr><th style="padding:1px;border: 1px solid black;background-color:#4149b5;  color: white;" colspan=12><center>PRODUCT SEARCH</center></th></tr>'
            data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;color:white;background-color:#6f6f6f;text-align: left"><b>Item Code</b></td><td colspan = 11 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(item)
            # data += '<tr><td colspan = 2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Item Name</b></td><td colspan = 3 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(frappe.db.get_value('Item',item,'item_name'))
            data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Description</b></td><td colspan = 11 style="padding:1px;border: 1px solid black;text-align: left" nowrap><b>%s</b></td></tr>'%(des)
            data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;text-align: left;background-color:#6f6f6f;color:white"><b>%s</b></td><td colspan = 11 style="padding:1px;border: 1px solid black;text-align: left;background-color:#FFFFFF;color:solid black"><b>%s</b></td></tr>'%(csp,f"{c_s_p:.2f}")
            data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;text-align: left"><b>Item Group</b></td><td colspan = 11 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(group)
            
            data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;color:white;background-color:#6f6f6f;text-align: left"><b>%s</b></td><td colspan = 11 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(pso,(del_total))
            if ppoc_total != 0.0:
                data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;color:white;background-color:#6f6f6f;text-align: left"><b>%s</b></td><td colspan = 11 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(ppo,(ppoc_total))
            else:
                data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;color:white;background-color:#6f6f6f;text-align: left"><b>%s</b></td><td colspan = 11 style="padding:1px;border: 1px solid black;text-align: left"><b>%s</b></td></tr>'%(ppo,(ppoc_total)) 
            
            if not frappe.session.user == "anoop@marazeemqatar.com":
                data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Company</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Item Code</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>QTY</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Res.qty</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>UOM</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>COST</b></center></td></tr>'
            
            if frappe.session.user == "anoop@marazeemqatar.com":
            
                if frappe.session.user == "anoop@marazeemqatar.com" and group == "Eyenor" or group == "NVS" or group == "Secnor":
                    data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Company</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Item Code</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>QTY</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Res.qty</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>UOM</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>COST</b></center></td></tr>'
                else:
                    data += '<tr><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Company</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Item Code</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>QTY</b></center></td><td colspan = 1 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>Res.qty</b></center></td><td colspan = 2 style="padding:1px;border: 1px solid black;background-color:#6f6f6f;color:white;"><center><b>UOM</b></center></td></tr>'

            product_bundle = frappe.get_doc("Product Bundle",self.item_code)
            for bundle in product_bundle.items:
                frappe.errprint(bundle.item_code)
                stocks = frappe.get_all(
                "Bin",
                filters={
                    "item_code": bundle.item_code,
                    "warehouse": ("not like", "%Work In Progress%"),
                },
                fields=["actual_qty", "warehouse", "stock_uom", "stock_value", "reserved_qty", "valuation_rate"]
            )

                warehouse_data = {}
                i = 0
                cou = 0
                reser =0
                tot = 'Total'
                if group=='OptiNor':
                    uom='Meter'
                # else:
                # 	uom = 'Nos'
                for stock in stocks:
                    # frappe.errprint(stock.warehouse)
                    valuation = round(stock['valuation_rate'],2)
                    comp = frappe.get_value("Warehouse", stock.warehouse, 'company')
                    entries = frappe.db.get_all("Stock Reservation Entry", 
                                                filters={"item_code": bundle.item_code, "warehouse": stock.warehouse,"status":("Not In",("Cancelled","Delivered")),"docstatus":("!=",2)}, 
                                                fields=["reserved_qty"])
                    total_reserved_qty = sum(flt(entry["reserved_qty"]) for entry in entries)
                    available_qty = stock.actual_qty
                    if comp in warehouse_data:
                        warehouse_data[comp]['available_qty'] += available_qty
                        warehouse_data[comp]['ppoc_total'] += total_reserved_qty
                        warehouse_data[comp]['del_total'] += del_total
                        warehouse_data[comp]['valuation'] =valuation
                    else:
                        warehouse_data[comp] = {
                            'available_qty': available_qty,
                            'ppoc_total': total_reserved_qty,
                            'del_total': del_total,
                            'valuation':valuation
                        }
                for comp, values in warehouse_data.items():
                    valuation = values['valuation']
                    if not frappe.session.user == "anoop@marazeemqatar.com":
                        if (values['available_qty'])-(values['ppoc_total'])>0:
                            data += '''
                                <tr>
                                    <td style="padding:1px;border: 1px solid;color:black;font-weight:bold" colspan=1 nowrap>{}</td>
                                    <td style="padding:1px;border: 1px solid;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                                    <td style="padding:1px;border: 1px solid;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                                    <td style="padding:1px;border: 1px solid;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                                    <td style="padding:1px;border: 1px solid;color:black;font-weight:bold;text-align:center" colspan=1>Meter</td>
                                    <td style="padding:1px;border: 1px solid;color:black;font-weight:bold;text-align:right" colspan=1>{}</td>
                                </tr>
                            '''.format(comp,bundle.item_code, round(values['available_qty'],2)-(values['ppoc_total']), (values['ppoc_total']), "{:.2f}".format(valuation))	

                            total_qty +=values['available_qty']
                            total_res +=values['ppoc_total']
            if not frappe.session.user == "anoop@marazeemqatar.com":
                data += '''
                    <tr>
                        <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                        <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                        <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                        <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                        <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                        <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:right" colspan=1>{}</td>
                    </tr>
                '''.format("Total"," " ,round(total_qty,2)-(total_res),(total_res),uom,"-")

            if frappe.session.user == "anoop@marazeemqatar.com":
                if group=='OptiNor':
                    data += '''
                        <tr>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:right" colspan=1>{}</td>
                        </tr>
                    '''.format("Total"," ",round(total_qty,2)-(total_res),(total_res),uom,"-")	

                elif frappe.session.user == "anoop@marazeemqatar.com" and group == "Eyenor" or group == "NVS" or group == "Secnor":
                    data += '''
                        <tr>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold;text-align:center" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                        </tr>
                    '''.format("Total"," " ,round(total_qty,2)-(total_res),(total_res),uom,"-")	

                
                else:
                    data += '''
                        <tr>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                            <td style="padding:1px;border: 1px solid black;background-color:#FFFFFF;color:black;font-weight:bold" colspan=1>{}</td>
                        </tr>
                    '''.format("Total"," " ,round(total_qty,2)-(total_res),(total_res),uom,"-")	
            data += '</table>'
            return data

    @frappe.whitelist()
    def get_data_taihan(self):
        date = frappe.db.get_value("Custom Settings", "Custom Settings", "date") or frappe.utils.today()

        item_code = self.item_code
        item = frappe.get_value('Item', {'item_code': item_code}, 'item_code')
        if not item:
            return '<p><b>Item not found!</b></p>'

        item_name = frappe.db.get_value('Item', item, 'item_name')
        group = frappe.get_value('Item', {'item_code': item_code}, 'item_group')
        description = frappe.get_value('Item', {'item_code': item_code}, 'description')
        uom = 'Nos'

        stocks_query = frappe.db.sql("""
            SELECT actual_qty, reserved_stock, warehouse, stock_uom, stock_value 
            FROM `tabBin` 
            WHERE item_code = %s
        """, (item,), as_dict=True)

        batch_names = []
        batch_records = frappe.get_all("Batch", filters={"disabled": 0, "batch_qty": (">", 0), "item": item}, fields=["name"])
        if batch_records:
            batch_names = [b["name"] for b in batch_records]
        batch = ", ".join(batch_names)

        
        data = '<table class="table table-bordered" style="width:70%">'
        data += '<tr><th colspan="12" style="padding:1px;border:1px solid black;background-color:#009ACD;color:white;"><center>Procurement Details</center></th></tr>'
        data += f'<tr><td colspan="2" style="padding:1px;border:1px solid black;color:black;text-align:left;"><b>Item Code</b></td><td colspan="8" style="padding:1px;border:1px solid black;text-align:left;">{item}</td></tr>'
        data += f'<tr><td colspan="2" style="padding:1px;border:1px solid black;color:black;text-align:left;"><b>Item Name</b></td><td colspan="8" style="padding:1px;border:1px solid black;text-align:left;">{item_name}</td></tr>'
        data += f'<tr><td colspan="2" style="padding:1px;border:1px solid black;color:black;text-align:left;"><b>Item Group</b></td><td colspan="8" style="padding:1px;border:1px solid black;text-align:left;">{group}</td></tr>'
        data += f'<tr><td colspan="2" style="padding:1px;border:1px solid black;color:black;text-align:left;"><b>Description</b></td><td colspan="8" style="padding:1px;border:1px solid black;text-align:left;">{description}</td></tr>'

        if stocks_query:
            data += '''
            <tr>
                <td colspan="2" style="padding:1px;border:1px solid black;color:white;background-color:#009ACD;"><center><b>Company</b></center></td>
                <td colspan="2" style="padding:1px;border:1px solid black;color:white;background-color:#009ACD;"><center><b>Warehouse</b></center></td>
                <td colspan="2" style="padding:1px;border:1px solid black;color:white;background-color:#009ACD;"><center><b>Qty</b></center></td>
                <td colspan="2" style="padding:1px;border:1px solid black;color:white;background-color:#009ACD;"><center><b>UOM</b></center></td>
                <td colspan="2" style="padding:1px;border:1px solid black;color:white;background-color:#009ACD;"><center><b>Batch</b></center></td>
            </tr>
            '''
            total_qty = 0
            for stock in stocks_query:
                reserve_qty = (stock.actual_qty or 0) - (stock.reserved_stock or 0)
                if reserve_qty <= 0:
                    continue

                company = frappe.db.get_value('Warehouse', stock.warehouse, 'company')
                if not company or company == "Norden Africa":
                    continue

                # Pending Sales Order
                so = frappe.db.sql("""
                    SELECT 
                        SUM(soi.qty) AS total_qty, 
                        SUM(soi.delivered_qty) AS delivered_qty 
                    FROM `tabSales Order Item` soi
                    LEFT JOIN `tabSales Order` so ON so.name = soi.parent
                    WHERE soi.item_code = %s AND so.docstatus = 1 AND so.status != 'Closed'
                    AND so.company = %s AND so.set_warehouse = %s AND so.transaction_date >= %s
                """, (item_code, company, stock.warehouse, date), as_dict=True)[0]
                pending_so_qty = (so.total_qty or 0) - (so.delivered_qty or 0)

                # Pending Purchase Order
                po = frappe.db.sql("""
                    SELECT 
                        SUM(poi.qty) AS total_qty, 
                        SUM(poi.received_qty) AS received_qty 
                    FROM `tabPurchase Order Item` poi
                    LEFT JOIN `tabPurchase Order` po ON po.name = poi.parent
                    WHERE poi.item_code = %s AND po.docstatus = 1 AND po.status != 'Closed'
                    AND po.company = %s AND po.set_warehouse = %s AND po.transaction_date >= %s
                """, (item_code, company, stock.warehouse, date), as_dict=True)[0]
                pending_po_qty = (po.total_qty or 0) - (po.received_qty or 0)

                if stock.actual_qty == 0 and pending_so_qty == 0 and pending_po_qty == 0:
                    continue

                data += f'''
                <tr>
                    <td colspan="2" style="padding:1px;border:1px solid black;"><center><b>{company}</b></center></td>
                    <td colspan="2" style="padding:1px;border:1px solid black;"><center><b>{stock.warehouse}</b></center></td>
                    <td colspan="2" style="padding:1px;border:1px solid black;"><center><b>{int(reserve_qty)}</b></center></td>
                    <td colspan="2" style="padding:1px;border:1px solid black;"><center><b>{stock.stock_uom or "-"}</b></center></td>
                    <td colspan="2" style="padding:1px;border:1px solid black;"><center><b>{batch}</b></center></td>
                </tr>
                '''
                total_qty += reserve_qty

            data += f'''
            <tr>
                <td align="right" colspan="4" style="padding:1px;border:1px solid black;color:white;background-color:#009ACD;"><b>Total</b></td>
                <td colspan="2" style="padding:1px;border:1px solid black;color:white;background-color:#009ACD;"><center><b>{int(total_qty)}</b></center></td>
                <td colspan="2" style="padding:1px;border:1px solid black;color:white;background-color:#009ACD;"><center><b>{uom}</b></center></td>
                <td colspan="2" style="padding:1px;border:1px solid black;color:white;background-color:#009ACD;"></td>
            </tr>
            '''
        else:
            data += '<tr><td align="center" colspan="10" style="padding:1px;border:1px solid black;background-color:#fe3f0c;color:white;"><b>No Stock Available</b></td></tr>'
        data += '</table>'

        
       
        return data
