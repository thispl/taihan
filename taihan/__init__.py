__version__ = "0.0.1"


def _patch_batch_incoming_rate():
	try:
		from erpnext.stock.serial_batch_bundle import BatchIncomingRate
		from frappe.utils import flt

		original_method = BatchIncomingRate.get_incoming_rate

		def safe_get_incoming_rate(self):
			actual_qty = flt(self.sle.actual_qty) or flt(self.get_actual_qty())
			if not actual_qty:
				return 0.0
			try:
				return original_method(self)
			except ZeroDivisionError:
				return 0.0

		BatchIncomingRate.get_incoming_rate = safe_get_incoming_rate
	except Exception:
		pass


_patch_batch_incoming_rate()
