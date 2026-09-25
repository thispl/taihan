
import frappe
from frappe.model.document import Document


#General Settings Code 
@frappe.whitelist()
def get_series(date,company,doctype):
    company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype,'with_tax':0},'series')
    return company_series




#Return the stock_balance for MR if so is in MR (onload)
@frappe.whitelist()
def return_mr_stock(company,item_code):
    warehouse_stock = frappe.db.sql("""
            SELECT SUM(b.actual_qty - b.reserved_stock) AS qty
            FROM `tabBin` AS b
            JOIN `tabWarehouse` AS wh ON wh.name = b.warehouse
            JOIN `tabCompany` AS c ON c.name = wh.company
            WHERE c.name = %s AND b.item_code = %s
        """, (company,item_code), as_dict=True)[0]
    return warehouse_stock



# set Res. Qty in MR in onload
@frappe.whitelist()
def get_qty_from_stock(so_no):
    items_data = {}
    stock = frappe.get_all('Stock Reservation Entry', {'voucher_no': so_no, 'docstatus': ('!=', '2')},
                           ['item_code', 'reserved_qty'])
    for entry in stock:
        item_code = entry.item_code
        reserved_qty = entry.reserved_qty
        if item_code in items_data:
            items_data[item_code] += reserved_qty
        else:
            items_data[item_code] = reserved_qty
    result = [{'item_code': item_code, 'reserved_qty': qty} for item_code, qty in items_data.items()]

    return result


# update SO qty in MR(onload)
@frappe.whitelist()
def get_salesorder_qty(so_no):
    sales_order = frappe.get_doc("Sales Order",so_no)
    return sales_order.items



# Aler mail for MR if the Qty is greater than ROL qty in Item
@frappe.whitelist()
def send_alert_mail_rol(doc, method):
    table_rows = ""
    # roles = ["", "HR Manager", "HOD"]
    for item in doc.items:
        item_doc = frappe.get_doc("Item", item.item_code)
        
        for i in item_doc.reorder_levels:
            if doc.set_warehouse == i.warehouse:
                rol_qty = i.warehouse_reorder_qty

                # Check if the current item qty exceeds the reorder level qty
                if item.qty > rol_qty:
                    table_rows += f"""
                    <tr>
                        <td style="border: 1px solid black; padding: 8px;">{item.item_code}</td>
                        <td style="border: 1px solid black; padding: 8px;">{item.qty}</td>
                        <td style="border: 1px solid black; padding: 8px;">{rol_qty}</td>
                    </tr>
                    """
    
    # Combine the emails of HR Manager and HR roles
    recipients = []
    user = frappe.get_all("User", filters={"role":("in",["Production Team","Store Department"]),'enabled':1},  fields=["email"])
    for j in user:
        recipients.append(j.email)
    # Send email only if there are items exceeding ROL
    if table_rows:
        message = f"""
            <p>The following items in Material Request <b>{doc.name}</b> have quantities exceeding their Reorder Level (ROL):</p>
            <table style="border-collapse: collapse; width: 100%; text-align: left;">
                <thead>
                    <tr>
                        <th style="border: 1px solid black; padding: 8px;">Item Code</th>
                        <th style="border: 1px solid black; padding: 8px;">Requested Qty</th>
                        <th style="border: 1px solid black; padding: 8px;">ROL Qty</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        """

        frappe.sendmail(
            recipients=recipients,
            subject=f"Item Qty Exceeds ROL in Material Request: {doc.name}",
            message=message
        )