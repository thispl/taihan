import frappe
from frappe.utils import today,formatdate, fmt_money

def get_count():


    # ===== 1. Submitted Orders =====
    so_list_submitted = frappe.get_all(
        "Sales Order",
        filters={
            "transaction_date": today(),
            "docstatus": 1
        },
        fields=["base_grand_total"]
    )
    total_count_submitted = len(so_list_submitted)
    total_value_submitted = sum(so.base_grand_total for so in so_list_submitted)
    total_value_submitted_fmt = total_value_submitted
    
    # s_person
    so_list = frappe.db.sql("""
        SELECT 
            so.transaction_date AS date,
            sp.sales_person AS sales_person,
            COUNT(so.name) AS so_count,
            SUM(so.base_grand_total) AS total_value
        FROM `tabSales Order` so
        LEFT JOIN `tabSales Team` sp ON sp.parent = so.name
        WHERE so.transaction_date = %s
          AND so.docstatus = 1
        GROUP BY sp.sales_person
        ORDER BY sp.sales_person
    """, today(), as_dict=True)

    # Calculate grand totals
    grand_total_count = sum(row.so_count for row in so_list)
    grand_total_value = sum(row.total_value for row in so_list)
    
    #cancelled _sales_p
    so_list_cancelled_sp = frappe.db.sql("""
        SELECT
            so.transaction_date AS date,
            sp.sales_person AS sales_person,
            COUNT(so.name) AS so_count,
            SUM(so.base_grand_total) AS total_value
        FROM `tabSales Order` so
        LEFT JOIN `tabSales Team` sp ON sp.parent = so.name
        WHERE so.transaction_date = %s
          AND so.docstatus = 2
        GROUP BY sp.sales_person
        ORDER BY sp.sales_person
    """, (today(),), as_dict=True)

    grand_total_count_cancel_sp = sum(row.get("so_count", 0) for row in so_list_cancelled_sp)
    grand_total_value_cancel_sp = sum(row.get("total_value", 0) for row in so_list_cancelled_sp)


    # ===== 2. Cancelled Orders =====
    so_list_cancelled = frappe.get_all(
        "Sales Order",
        filters={
            "transaction_date": today(),
            "docstatus": 2
        },
        fields=["base_grand_total"]
    )
    total_count_cancelled = len(so_list_cancelled)
    total_value_cancelled = sum(so.base_grand_total for so in so_list_cancelled)
    total_value_cancelled_fmt = total_value_cancelled

    # ===== HTML for both tables =====
    # html_content =""
    # html_content = f"""
    # <p>Dear Team,</p>

    # <p>Please find below the details of <b>Sales Orders</b> (Date Wise Status):</p>
    # """

    # if total_count_submitted > 0:
    #     html_content += f"""
    # <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px;">
    #     <tr>
    #         <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">Incoming SO Value<br>Date wise Status</td>
    #     </tr>
    #     <tr style="background-color:#dee9ec; font-weight:bold;">
    #         <td>Date</td>
    #         <td>No Of SO's Processed</td>
    #         <td>Total SO Value</td>
    #     </tr>
    #     <tr>
    #         <td>{formatdate(today())}</td>
    #         <td>{total_count_submitted}</td>
    #         <td>{fmt_money(total_value_submitted_fmt,2)}</td>
    #     </tr>
    #     <tr style="background-color:#a7d3e0;font-weight:bold;"">
    #         <td style="background-color:#a7d3e0;font-weight:bold;">Grand Total</td>
    #         <td>{total_count_submitted}</td>
    #         <td>{fmt_money(total_value_submitted_fmt,2)}</td>
    #     </tr>
    # </table>
    # """
    # else:
    # # No sales orders today
    #     html_content += f"""
    
    #     <table border="1"  style="border-collapse:collapse; text-align:center; margin-bottom:20px;">
    
    #     <tr>
    #         <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">
    #             Incoming SO Value<br>Date wise Status
    #         </td>
    #     </tr>
    #      <tr style="background-color:#dee9ec; font-weight:bold;padding:10px;">
    #         <td>Date</td>
    #         <td>No Of SO's Processed</td>
    #         <td>Total SO Value</td>
    #     </tr>
    #     <tr>
    #         <td colspan="3" style="padding:10px; color:red; font-weight:bold;">
    #             No Sales Orders for {formatdate(today())}
    #         </td>
    #     </tr>
    # </table>
    # """
    
    
    # if so_list:
    #     html_content += f"""
    #     <br><br><br>
    #     <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px;">
    #     <tr>
    #         <td colspan="4" style="background-color:#a7d3e0;font-weight:bold;">
    #             Incoming SO Value<br>
    #             Date & Sales Person wise Status
    #         </td>
    #     </tr>
    #     <tr style="background-color:#dee9ec; font-weight:bold;">
    #         <td>Date</td>
    #         <td>Sales Person</td>
    #         <td>No Of SO's</td>
    #         <td>Total SO Value</td>
    #     </tr>
    #     """

    

    #     for row in so_list:
    #         html_content += f"""
    #     <tr>
    #     <td>{formatdate(today())}</td>
    #     <td>{row.sales_person or ''}</td>
    #     <td>{row.so_count or 0}</td>
    #     <td>{fmt_money(row.total_value,2) or 0}</td>
    #     </tr>
    #     """


    #     html_content += f"""
    #     <tr style="background-color:#a7d3e0; font-weight:bold;">
    #     <td colspan="2">Grand Total</td>
    #     <td></td>
    #     <td>{grand_total_count or 0}</td>
    #     <td>{fmt_money(grand_total_value,2) or 0}</td>
    #     </tr>
    #     </table>
    #     """
    # else:
    # # No sales person today
    
    #     html_content += f"""
    #      <br><br><br>
    #     <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px;">
    
    #     <tr>
    #         <td colspan="4" style="background-color:#a7d3e0;font-weight:bold;">
    #             Incoming SO Value<br>Date wise Status
    #         </td>
    #     </tr>
    #     <tr style="background-color:#dee9ec; font-weight:bold;">
    #         <td>Date</td>
    #         <td>Sales Person</td>
    #         <td>No Of SO's</td>
    #         <td>Total SO Value</td>
    #     </tr>
    #     <tr>
    #         <td colspan="4" style="padding:10px; color:red; font-weight:bold;">
    #             No sales person  {formatdate(today())}
    #         </td>
    #     </tr>
    #     </table>
    #     """

    # if total_count_cancelled > 0 :
    #     html_content += f""" 
    #     <br><br><br>
    #     <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px;">
    #     <tr>
    #         <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">Cancelled SO Value<br>Date wise Status</td>
    #     </tr>
    #     <tr style="background-color:#dee9ec; font-weight:bold;">
    #         <td>Date</td>
    #         <td>No Of SO's Processed</td>
    #         <td>Total SO Value</td>
    #     </tr>
    #     <tr>
    #         <td>{formatdate(today())}</td>
    #         <td>{total_count_cancelled}</td>
    #         <td>{fmt_money(total_value_cancelled_fmt,2)}</td>
    #     </tr>
    #     <tr style="background-color:#a7d3e0;font-weight:bold;">
    #         <td>Grand Total</td>
    #         <td>{total_count_cancelled}</td>
    #         <td>{fmt_money(total_value_cancelled_fmt,2)}</td>
    #     </tr>
    #     </table>
    #     """
    # else :
    #     html_content += f"""
    #     <br><br><br>
    #     <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px;">
    
    #     <tr>
    #         <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">
    #             Cancelled SO Value<br>Date wise Status
    #         </td>
    #     </tr>
    #      <tr style="background-color:#dee9ec; font-weight:bold;">
    #         <td>Date</td>
    #         <td>No Of SO's Processed</td>
    #         <td>Total SO Value</td>
    #     </tr>
    #     <tr>
    #         <td colspan="3" style="padding:10px; color:red; font-weight:bold;">
    #             No Cancel Sales Orders for {formatdate(today())}
    #         </td>
    #     </tr>
    # </table>
    # """
    
    # # cancelled
    # html_content += """
    # <br><br>
    # <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px;">
    #     <tr>
    #         <td colspan="4" style="background-color:#a7d3e0;font-weight:bold;">Cancelled SO Value<br>Date & Sales Person wise Status</td>
    #     </tr>
    #     <tr style="background-color:#dee9ec; font-weight:bold;">
    #         <td>Date</td>
    #         <td>Sales Person</td>
    #         <td>No Of SO's</td>
    #         <td>Total SO Value</td>
    #     </tr>
    # """

    # if so_list_cancelled_sp:
    #     for row in so_list_cancelled_sp:
    #         html_content += f"""
    #         <tr>
    #             <td>{formatdate(today())}</td>
    #             <td>{row.get('sales_person') or ''}</td>
    #             <td>{row.get('so_count') or 0}</td>
    #             <td>{fmt_money(row.get('total_value'),2) or 0}</td>
    #         </tr>
    #         """
    #     html_content += f"""
    #     <tr style="background-color:#a7d3e0; font-weight:bold;">
    #         <td>{today()}</td>
    #         <td>Grand Total</td>
    #         <td>{grand_total_count_cancel_sp or 0}</td>
    #         <td>{fmt_money(grand_total_value_cancel_sp,2) or 0}</td>
    #     </tr>
    #     """
    # else:
    #     html_content += f"""
    #     <tr>
    #         <td colspan="4" style="padding:10px; color:red; font-weight:bold;">
    #             No  Cancel Sales Oredr in Sales Person  {formatdate(today())}
    #         </td>
    #     </tr>
    #     """

    # html_content += "</table>"
    html_content = ""
    html_content = f"""
        <p>Dear Team,</p>

    <p>Please find below the details of <b>Sales Orders</b> (Date Wise Status):</p>
    """

    if total_count_submitted > 0:
        html_content += f"""
        <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
        <tr>
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">Incoming SO Value<br>Date wise Status</td>
        </tr>
        <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>No Of SO's Processed</td>
        <td>Total SO Value</td>
        </tr>
        <tr>
        <td>{formatdate(today())}</td>
        <td>{total_count_submitted}</td>
        <td style="text-align:right;">{fmt_money(total_value_submitted_fmt,2)}</td>
        </tr>
        <tr style="background-color:#a7d3e0;font-weight:bold;"">
        <td style="background-color:#a7d3e0;font-weight:bold;">Grand Total</td>
        <td>{total_count_submitted}</td>
        <td style="text-align:right;">{fmt_money(total_value_submitted_fmt,2)}</td>
        </tr>
        </table>
        """
    else:
    # No sales orders today
        html_content += f"""
<table border="1" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
<tr>
    <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">
        Incoming SO Value<br>Date wise Status
    </td>
</tr>
 <tr style="background-color:#dee9ec; font-weight:bold;padding:10px;">
    <td>Date</td>
    <td>No Of SO's Processed</td>
    <td>Total SO Value</td>
</tr>
<tr>
    <td colspan="3" style="padding:10px; color:red; font-weight:bold;">
        No Sales Orders for {formatdate(today())}
    </td>
</tr>
</table>
"""

    if so_list:
        html_content += f"""
    <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="4" style="background-color:#a7d3e0;font-weight:bold;">
            Incoming SO Value<br>
            Date & Sales Person wise Status
        </td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>Sales Person</td>
        <td>No Of SO's</td>
        <td>Total SO Value</td>
    </tr>
    """

        for row in so_list:
            html_content += f"""
    <tr>
    <td>{formatdate(today())}</td>
    <td style="text-align:left;">{row.sales_person or ''}</td>
    <td>{row.so_count or 0}</td>
    <td style="text-align:right;">{fmt_money(row.total_value,2) or 0}</td>
    </tr>
    """

        html_content += f"""
    <tr style="background-color:#a7d3e0; font-weight:bold;">
    <td colspan="2">Grand Total</td>
    <td>{grand_total_count or 0}</td>
    <td style="text-align:right;">{fmt_money(grand_total_value,2) or 0}</td>
    </tr>
    </table>
    """
    else:
    # No sales person today
        html_content += f"""
     <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
<tr>
    <td colspan="4" style="background-color:#a7d3e0;font-weight:bold;">
        Incoming SO Value<br>Date wise Status
    </td>
</tr>
<tr style="background-color:#dee9ec; font-weight:bold;">
    <td>Date</td>
    <td>Sales Person</td>
    <td>No Of SO's</td>
    <td>Total SO Value</td>
</tr>
<tr>
    <td colspan="4" style="padding:10px; color:red; font-weight:bold;">
        No Submitted Sales Oredr In Sales Person  {formatdate(today())}
    </td>
</tr>
</table>
"""

    if total_count_cancelled > 0 :
        html_content += f""" 
    <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">Cancelled SO Value<br>Date wise Status</td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>No Of SO's Processed</td>
        <td>Total SO Value</td>
    </tr>
    <tr>
        <td>{formatdate(today())}</td>
        <td>{total_count_cancelled}</td>
        <td style="text-align:right;">{fmt_money(total_value_cancelled_fmt,2)}</td>
    </tr>
    <tr style="background-color:#a7d3e0;font-weight:bold;">
        <td>Grand Total</td>
        <td>{total_count_cancelled}</td>
        <td style="text-align:right;">{fmt_money(total_value_cancelled_fmt,2)}</td>
    </tr>
    </table>
    """
    else :
        html_content += f"""
    <br><br><br>
    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
<tr>
    <td colspan="3" style="background-color:#a7d3e0;font-weight:bold;">
        Cancelled SO Value<br>Date wise Status
    </td>
</tr>
 <tr style="background-color:#dee9ec; font-weight:bold;">
    <td>Date</td>
    <td>No Of SO's Processed</td>
    <td>Total SO Value</td>
</tr>
<tr>
    <td colspan="3" style="padding:10px; color:red; font-weight:bold;">
        No Cancel Sales Orders for {formatdate(today())}
    </td>
</tr>
</table>
"""

# cancelled
    html_content += """
<br><br>
<table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse; text-align:center; margin-bottom:20px; width:100%; table-layout:fixed;">
    <tr>
        <td colspan="4" style="background-color:#a7d3e0;font-weight:bold;">Cancelled SO Value<br>Date & Sales Person wise Status</td>
    </tr>
    <tr style="background-color:#dee9ec; font-weight:bold;">
        <td>Date</td>
        <td>Sales Person</td>
        <td>No Of SO's</td>
        <td>Total SO Value</td>
    </tr>
"""
    if so_list_cancelled_sp:
        for row in so_list_cancelled_sp:
            html_content += f"""
        <tr>
            <td style="text-align:left;">{formatdate(today())}</td>
            <td>{row.get('sales_person') or ''}</td>
            <td>{row.get('so_count') or 0}</td>
            <td style="text-align:right;">{fmt_money(row.get('total_value'),2) or 0}</td>
        </tr>
        """
        html_content += f"""
        <tr style="background-color:#a7d3e0; font-weight:bold;">
        <td>{today()}</td>
        <td>Grand Total</td>
        <td>{grand_total_count_cancel_sp or 0}</td>
        <td style="text-align:right;">{fmt_money(grand_total_value_cancel_sp,2) or 0}</td>
    </tr>
    """
    else:
        html_content += f"""
    <tr>
        <td colspan="4" style="padding:10px; color:red; font-weight:bold;">
            No  Cancel Sales Order in Sales Person  {formatdate(today())}
        </td>
    </tr>
    """

    html_content += "</table>"
        

    # ===== Send email =====
    frappe.sendmail(
        sender="muthuselvan.e@groupteampro.com",
        recipients="divya.p@groupteampro.com",
        subject=f"Today's Sales Order Summary - {formatdate(today())}",
        message=html_content
    )

    print("Email sent successfully!")
