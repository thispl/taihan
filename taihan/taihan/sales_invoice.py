from __future__ import unicode_literals
import frappe,erpnext
from frappe.utils import cint
from frappe.utils import flt, fmt_money
import json
from frappe.utils import date_diff, add_months,today,add_days,add_years,nowdate,flt
from frappe.utils import cstr, cint, getdate,get_first_day, get_last_day, today, time_diff_in_hours

from frappe.model.mapper import get_mapped_doc
from frappe.utils.file_manager import get_file
from frappe.utils.csvutils import UnicodeWriter, read_csv_content
import datetime
from datetime import date,datetime,timedelta
import openpyxl
from collections import defaultdict
from openpyxl import Workbook
import openpyxl
import xlrd
import re
from frappe.utils import date_diff,today,cstr
from datetime import datetime
from dateutil import relativedelta
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import GradientFill, PatternFill
from frappe.utils import formatdate


from erpnext.setup.utils import get_exchange_rate
from frappe import throw,_, db, get_doc, throw, whitelist


from frappe.utils import (
    add_days,
    cint,
    cstr,
    date_diff,
    flt,
    formatdate,
    get_first_day,
    get_link_to_form,
    getdate,
    money_in_words,
    rounded,
)


#Show the below details in HTML View while click the button oF Margin details in QN
@frappe.whitelist()
def get_item_margin(item_details,company,discount_amount):
    item_details = json.loads(item_details)
    data_4 = ''
    data_4 += '''<table class="table">
    <tr>
    <th style="padding:1px;border: 1px solid black;font-size:14px;background-color:#FF4500;color:white;" colspan =9 ><center><b>MARGIN</b></center></th>
    </tr>'''

    data_4+='''<tr>
    <td colspan=1 style="border: 1px solid black;font-size:12px;"><b>ITEM</b></td>
    <td colspan=1 style="border: 1px solid black;font-size:12px;"><b>ITEM NAME</b></td>
    <td colspan=1 style="border: 1px solid black;font-size:12px;"><b><center>QTY</center></b></td>
    <td colspan=1 style="border: 1px solid black;font-size:12px;"><b><center>Selling Price</center></b></td>
    <td colspan=1 style="border: 1px solid black;font-size:12px;"><b><center>Cost</center></b></td>
    <td colspan=1 style="border: 1px solid black;font-size:12px;"><b><center>Selling Amount</center></b></td>
    <td colspan=1 style="border: 1px solid black;font-size:12px;"><b><center>Cost Amount</center></b></td>
    <td colspan=1 style="border: 1px solid black;font-size:12px;"><b><center>Profit Amount</center></b></td>
    <td colspan=1 style="border: 1px solid black;font-size:12px;"><b><center>Profit %</center></b></td>
    </tr>'''
    cost_amount = 0
    total_selling_price = 0
    rate = 0
    cost = 0
    selling_amount = 0
    profit_amount_ = 0
    selling_amount_ = 0
    qty_tot = 0
    tot_per = 0
    tot =0
    no_item = 0
    for i in item_details:
        qty_tot += i["qty"]
        rate += i["base_net_rate"]
        selling_amount += i["base_net_amount"]
        total_selling_price = (i["base_net_rate"] * i["qty"]) + total_selling_price
        
        bom = frappe.db.get_value("Sales Order Item",{"parent":i["sales_order"],"item_code":i["item_code"]},["bom_no"])
        bom_cost = frappe.db.get_value("BOM",{"name":bom},["total_cost"])
        bom_cost_amount = bom_cost * i["qty"]
        cost += bom_cost
        cost_amount += bom_cost_amount		
        
        tot_diff = i["base_net_amount"] - bom_cost_amount
        tot += tot_diff
        if bom_cost > 0:
            tot_ = tot_diff / bom_cost * 100
            tot_per += tot_
            
            data_4 += '''<tr>
                <td colspan=1 style="border: 1px solid black;font-size:12px;">{}</td>
                <td colspan=1 style="border: 1px solid black;font-size:12px;">{}</td>
                <td colspan=1 style="border: 1px solid black;font-size:12px; text-align: right">{}</td>
                <td colspan=1 style="border: 1px solid black;font-size:12px; text-align: right">{}</td>
                <td colspan=1 style="border: 1px solid black;font-size:12px; text-align: right">{}</td>
                <td colspan=1 style="border: 1px solid black;font-size:12px; text-align: right">{}</td>
                <td colspan=1 style="border: 1px solid black;font-size:12px; text-align: right">{}</td>
                <td colspan=1 style="border: 1px solid black;font-size:12px; text-align: right">{}</td>
                <td colspan=1 style="border: 1px solid black;font-size:12px; text-align: right">{}</td>
            </tr>'''.format(i["item_code"], i["description"], i["qty"],round(i["base_net_rate"], 2),round(bom_cost,2) ,round(i["base_net_amount"], 2),round(bom_cost_amount,2) , round(tot_diff, 2), round(tot_, 2))
        
    data_4 += '''<tr>
    <td colspan=2 style="border: 1px solid black;padding:1px;font-size:14px;text-align: right"><b>Total </b></td>
    <td style="border: 1px solid black;padding:1px;font-size:12px;text-align: right"><b>%s</b></td>
    <td style="border: 1px solid black;padding:1px;font-size:12px;text-align: right"><b>%s</b></td>
    <td style="border: 1px solid black;padding:1px;font-size:12px;text-align: right"><b>%s</b></td>
    <td style="border: 1px solid black;padding:1px;font-size:12px;text-align: right"><b>%s</b></td>
    <td style="border: 1px solid black;padding:1px;font-size:12px;text-align: right"><b>%s</b></td>
    <td style="border: 1px solid black;padding:1px;font-size:12px;text-align: right"><b>%s</b></td>
    <td style="border: 1px solid black;padding:1px;font-size:12px;text-align: right"><b>%s</b></td>
    </tr>'''%(qty_tot,round(rate,2),round(cost,2),round(selling_amount,2),round(cost_amount,2),round(tot,2),round(tot_per,2))

    return data_4



@frappe.whitelist()
def get_series(date,company,doctype):
    company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype,'with_tax':0},'series')
    return company_series