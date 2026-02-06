# Copyright (c) 2026, Custom Clearance and Contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, flt, get_fullname
from frappe import _


class CustomClearance(Document):
	def validate(self):
		"""Validate document before save"""
		# Auto-change status to Review when all mandatory documents are accepted
		if self.status == "Document Submitting" and self.required_documents:
			all_mandatory_accepted = True
			has_required_docs = False
			for req_doc in self.required_documents:
				if req_doc.is_required:
					has_required_docs = True
					if req_doc.status != "Accepted":
						all_mandatory_accepted = False
						break
			
			if has_required_docs and all_mandatory_accepted:
				self.status = "In Review"
		
		# Validate status transitions
		if self.has_value_changed("status"):
			self.validate_status_transition()
		
		# Note: Payment notifications are now handled via the send_payment_notification method
		# when staff clicks the "Send Notification" button in the payment table
	
	def validate_status_transition(self):
		"""Validate status transitions"""
		# Can only move from In Review to Risk Analysis
		if self.status == "Risk Analysis" and self._doc_before_save:
			if self._doc_before_save.status not in ["In Review", "Risk Analysis"]:
				frappe.throw(_("Status can only be changed to Risk Analysis from In Review"))
		
		# Can only move from Risk Analysis to Cleared
		if self.status == "Cleared" and self._doc_before_save:
			if self._doc_before_save.status not in ["Risk Analysis", "Cleared"]:
				frappe.throw(_("Status can only be changed to Cleared from Risk Analysis"))
		
		# Note: Payment validation is now handled via the payments child table
		# Staff can add payments when status is "In Review" or "Risk Analysis"


@frappe.whitelist()
def get_template_documents(template):
	"""Get documents from a template"""
	if not template:
		return []
	
	template_doc = frappe.get_doc("Custom Clearance Template", template)
	documents = []
	
	for doc in template_doc.required_documents:
		documents.append({
			"document_name": doc.document_name,
			"is_required": doc.is_required,
			"has_sub_items": doc.has_sub_items,
			"sub_items": doc.sub_items
		})
	
	return documents


@frappe.whitelist()
def create_sales_invoice(source_name):
	"""Create Sales Invoice from Custom Clearance - returns invoice name for redirect"""
	custom_clearance = frappe.get_doc("Custom Clearance", source_name)
	
	# Check if sales invoice already exists
	if custom_clearance.sales_invoice:
		frappe.throw("Sales Invoice already created: {0}".format(
			frappe.get_desk_link("Sales Invoice", custom_clearance.sales_invoice)
		))
	
	# Get service item for custom clearance
	service_item = frappe.db.get_value("Item", {"item_code": "Custom Clearance Service"}, "name")
	if not service_item:
		frappe.throw("Custom Clearance Service item not found. Please ensure it is created during app installation.")
	
	# Create Sales Invoice (don't submit, let user review and submit)
	sales_invoice = frappe.get_doc({
		"doctype": "Sales Invoice",
		"customer": custom_clearance.customer,
		"posting_date": today(),
		"due_date": today(),
		"items": [{
			"item_code": service_item,
			"qty": 1,
			"rate": flt(custom_clearance.amount) if custom_clearance.amount else 0
		}]
	})
	
	# Add custom field link to Custom Clearance if it exists
	if frappe.db.has_column("Sales Invoice", "custom_custom_clearance"):
		sales_invoice.set("custom_custom_clearance", custom_clearance.name)
	
	sales_invoice.insert()
	
	# Update Custom Clearance with Sales Invoice link
	custom_clearance.db_set("sales_invoice", sales_invoice.name)
	
	return {"invoice_name": sales_invoice.name}


def update_clearance_payment_status(doc, method):
	"""Update Custom Clearance payment status when Sales Invoice status changes"""
	# Check if this Sales Invoice is linked to a Custom Clearance
	custom_clearance = frappe.db.get_value("Custom Clearance", {"sales_invoice": doc.name}, "name")
	if custom_clearance:
		# Map Sales Invoice status to payment status
		# Handle all possible statuses including discounted variants
		if doc.status == "Paid":
			payment_status = "Paid"
		elif doc.status in ("Partly Paid", "Partly Paid and Discounted"):
			payment_status = "Partially Paid"
		elif doc.status in ("Draft", "Unpaid", "Overdue", "Unpaid and Discounted", 
		                   "Overdue and Discounted", "Submitted", "Cancelled", 
		                   "Return", "Credit Note Issued", "Internal Transfer"):
			payment_status = "Pending"
		else:
			payment_status = "Pending"
		
		# Update payment status
		frappe.db.set_value("Custom Clearance", custom_clearance, "payment_status", payment_status)
		
		# If paid, update payment date
		if doc.status == "Paid":
			frappe.db.set_value("Custom Clearance", custom_clearance, "payment_date", today())


def handle_sales_invoice_cancel(doc, method):
	"""Handle Sales Invoice cancellation - unlink from Custom Clearance and reset status"""
	# Find Custom Clearance linked to this Sales Invoice
	custom_clearance = frappe.db.get_value("Custom Clearance", {"sales_invoice": doc.name}, "name")
	if custom_clearance:
		# Unlink the sales invoice
		frappe.db.set_value("Custom Clearance", custom_clearance, "sales_invoice", None)
		
		# Reset payment status to Pending
		frappe.db.set_value("Custom Clearance", custom_clearance, "payment_status", "Pending")
		
		# Clear payment date
		frappe.db.set_value("Custom Clearance", custom_clearance, "payment_date", None)
		
		# If status is Green/Yellow/Red, change it back to Review
		current_status = frappe.db.get_value("Custom Clearance", custom_clearance, "status")
		if current_status in ["Green", "Yellow", "Red"]:
			frappe.db.set_value("Custom Clearance", custom_clearance, "status", "Review")


@frappe.whitelist()
def update_document_attachment(clearance_name, row_name, file_url, is_reupload=False):
	"""Update attachment for a specific document in the required_documents child table"""
	# Check permissions
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to upload documents"), frappe.PermissionError)
	
	# Get the custom clearance document
	clearance = frappe.get_doc("Custom Clearance", clearance_name)
	
	# Check permissions - user must be linked to the customer
	if frappe.session.user != "Administrator":
		# Get customer linked to the current user
		customer = None
		contact = frappe.db.get_value("Contact", {"user": frappe.session.user}, "name")
		if contact:
			contact_doc = frappe.get_doc("Contact", contact)
			for link in contact_doc.links:
				if link.link_doctype == "Customer":
					customer = link.link_name
					break
		
		# If still no customer, try Portal User
		if not customer:
			portal_users = frappe.get_all(
				"Portal User",
				filters={"user": frappe.session.user, "parenttype": "Customer"},
				fields=["parent"],
				limit=1
			)
			if portal_users:
				customer = portal_users[0].parent
		
		# Check if user has permission to update this clearance
		if not customer or clearance.customer != customer:
			frappe.throw(_("You don't have permission to update this Custom Clearance"), frappe.PermissionError)
	
	# Find the document row and update it
	found = False
	for req_doc in clearance.required_documents:
		if req_doc.name == row_name:
			req_doc.attachment = file_url
			# If this is a re-upload after decline, reset status to "In Review"
			if is_reupload and req_doc.status == "Declined":
				req_doc.status = "In Review"
				req_doc.reason = None  # Clear the decline reason
			found = True
			break
	
	if not found:
		frappe.throw(_("Document row not found"), frappe.DoesNotExistError)
	
	# Save the document
	clearance.save(ignore_permissions=True)
	frappe.db.commit()
	
	return {"success": True, "message": _("Document attached successfully")}


@frappe.whitelist()
def update_document_status(clearance_name, row_name, status, reason=None):
	"""Update status for a specific document in the required_documents child table"""
	# Check permissions
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to update document status"), frappe.PermissionError)
	
	# Get the custom clearance document
	clearance = frappe.get_doc("Custom Clearance", clearance_name)
	
	# Check permissions - user must be linked to the customer or be admin/staff
	is_customer = False
	if frappe.session.user != "Administrator":
		# Get customer linked to the current user
		customer = None
		contact = frappe.db.get_value("Contact", {"user": frappe.session.user}, "name")
		if contact:
			contact_doc = frappe.get_doc("Contact", contact)
			for link in contact_doc.links:
				if link.link_doctype == "Customer":
					customer = link.link_name
					break
		
		# If still no customer, try Portal User
		if not customer:
			portal_users = frappe.get_all(
				"Portal User",
				filters={"user": frappe.session.user, "parenttype": "Customer"},
				fields=["parent"],
				limit=1
			)
			if portal_users:
				customer = portal_users[0].parent
		
		# Check if user has permission to update this clearance
		if customer and clearance.customer == customer:
			is_customer = True
		elif not customer or clearance.customer != customer:
			frappe.throw(_("You don't have permission to update this Custom Clearance"), frappe.PermissionError)
	
	# Find the document row and update it
	found = False
	for req_doc in clearance.required_documents:
		if req_doc.name == row_name:
			req_doc.status = status
			if reason:
				req_doc.reason = reason
			found = True
			break
	
	if not found:
		frappe.throw(_("Document row not found"), frappe.DoesNotExistError)
	
	# Save the document
	clearance.save(ignore_permissions=True)
	frappe.db.commit()
	
	# Check if all mandatory documents are accepted and auto-change status
	if clearance.status == "Document Submitting" and clearance.required_documents:
		all_mandatory_accepted = True
		for req_doc in clearance.required_documents:
			if req_doc.is_required:
				if req_doc.status != "Accepted":
					all_mandatory_accepted = False
					break
		
		if all_mandatory_accepted:
			clearance.db_set("status", "Review")
	
	return {"success": True, "message": _("Document status updated successfully")}


@frappe.whitelist()
def update_clearance_status(clearance_name, status, comment=None, additional_payment_amount=None):
	"""Update the overall clearance status"""
	# Check permissions
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to update status"), frappe.PermissionError)
	
	# Get the custom clearance document
	clearance = frappe.get_doc("Custom Clearance", clearance_name)
	
	# Check permissions - staff/admin can update, customers can only view
	is_customer = False
	if frappe.session.user != "Administrator":
		# Get customer linked to the current user
		customer = None
		contact = frappe.db.get_value("Contact", {"user": frappe.session.user}, "name")
		if contact:
			contact_doc = frappe.get_doc("Contact", contact)
			for link in contact_doc.links:
				if link.link_doctype == "Customer":
					customer = link.link_name
					break
		
		if not customer:
			portal_users = frappe.get_all(
				"Portal User",
				filters={"user": frappe.session.user, "parenttype": "Customer"},
				fields=["parent"],
				limit=1
			)
			if portal_users:
				customer = portal_users[0].parent
		
		if customer and clearance.customer == customer:
			is_customer = True
		# Only staff/admin can change status, customers can only view
		if is_customer:
			frappe.throw(_("You don't have permission to change the clearance status"), frappe.PermissionError)
	
	# Update status
	clearance.status = status
	if comment:
		clearance.risk_status_comment = comment
	if additional_payment_amount:
		clearance.additional_payment_amount = flt(additional_payment_amount)
	
	clearance.save(ignore_permissions=True)
	frappe.db.commit()
	
	return {"success": True, "message": _("Status updated successfully")}


@frappe.whitelist()
def add_comment(clearance_name, content, payment_amount=None, attachment_url=None):
	"""Add a comment to the custom clearance"""
	# Check permissions
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to add comments"), frappe.PermissionError)
	
	# Get the custom clearance document
	clearance = frappe.get_doc("Custom Clearance", clearance_name)
	
	# Check permissions - user must be linked to the customer
	if frappe.session.user != "Administrator":
		customer = None
		contact = frappe.db.get_value("Contact", {"user": frappe.session.user}, "name")
		if contact:
			contact_doc = frappe.get_doc("Contact", contact)
			for link in contact_doc.links:
				if link.link_doctype == "Customer":
					customer = link.link_name
					break
		
		if not customer:
			portal_users = frappe.get_all(
				"Portal User",
				filters={"user": frappe.session.user, "parenttype": "Customer"},
				fields=["parent"],
				limit=1
			)
			if portal_users:
				customer = portal_users[0].parent
		
		if not customer or clearance.customer != customer:
			frappe.throw(_("You don't have permission to comment on this Custom Clearance"), frappe.PermissionError)
	
	# Build comment content (no attachments allowed)
	comment_content = content
	if payment_amount:
		comment_content += f"\n\n<b>Additional Payment Required: {frappe.format_value(payment_amount, {'fieldtype': 'Currency'})}</b>"
	# Removed attachment_url support as per user request
	
	# Create comment using Frappe's Comment doctype
	comment = frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Comment",
		"reference_doctype": "Custom Clearance",
		"reference_name": clearance_name,
		"content": comment_content,
		"comment_email": frappe.session.user,
		"comment_by": get_fullname(frappe.session.user),
		"published": 1
	})
	comment.insert(ignore_permissions=True)
	frappe.db.commit()
	
	return {"success": True, "message": _("Comment added successfully"), "comment_name": comment.name}


@frappe.whitelist()
def get_comments(clearance_name):
	"""Get all comments for a custom clearance"""
	# Check permissions
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to view comments"), frappe.PermissionError)
	
	# Get the custom clearance document
	clearance = frappe.get_doc("Custom Clearance", clearance_name)
	
	# Check permissions - user must be linked to the customer
	if frappe.session.user != "Administrator":
		customer = None
		contact = frappe.db.get_value("Contact", {"user": frappe.session.user}, "name")
		if contact:
			contact_doc = frappe.get_doc("Contact", contact)
			for link in contact_doc.links:
				if link.link_doctype == "Customer":
					customer = link.link_name
					break
		
		if not customer:
			portal_users = frappe.get_all(
				"Portal User",
				filters={"user": frappe.session.user, "parenttype": "Customer"},
				fields=["parent"],
				limit=1
			)
			if portal_users:
				customer = portal_users[0].parent
		
		if not customer or clearance.customer != customer:
			frappe.throw(_("You don't have permission to view comments for this Custom Clearance"), frappe.PermissionError)
	
	# Get comments
	comments = frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": "Custom Clearance",
			"reference_name": clearance_name,
			"comment_type": "Comment",
			"published": 1
		},
		fields=["name", "content", "comment_by", "comment_email", "creation", "owner"],
		order_by="creation asc"
	)
	
	# Determine if each comment is from customer or staff
	result = []
	for comment in comments:
		comment_dict = {
			"name": comment.name,
			"content": comment.content,
			"comment_by": comment.comment_by or comment.comment_email,
			"comment_email": comment.comment_email,
			"creation": comment.creation,
			"owner": comment.owner
		}
		
		# Check if comment is from customer
		is_customer = False
		if comment.owner != "Administrator":
			customer = None
			user_doc = frappe.get_doc("User", comment.owner)
			contact = frappe.db.get_value("Contact", {"user": comment.owner}, "name")
			if contact:
				contact_doc = frappe.get_doc("Contact", contact)
				for link in contact_doc.links:
					if link.link_doctype == "Customer":
						customer = link.link_name
						break
			
			if not customer:
				portal_users = frappe.get_all(
					"Portal User",
					filters={"user": comment.owner, "parenttype": "Customer"},
					fields=["parent"],
					limit=1
				)
				if portal_users:
					customer = portal_users[0].parent
			
			if customer and clearance.customer == customer:
				is_customer = True
		
		comment_dict["is_customer"] = is_customer
		result.append(comment_dict)
	
	return {"success": True, "comments": result}


@frappe.whitelist()
def save_payment_info(clearance_name, payment_type, amount=None, branch=None, account_number=None, custom_id_code=None):
	"""Save payment information and create notification"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to save payment information"), frappe.PermissionError)
	
	# Get the custom clearance document
	clearance = frappe.get_doc("Custom Clearance", clearance_name)
	
	# Check if user is staff/admin
	is_staff = False
	if frappe.session.user == "Administrator":
		is_staff = True
	else:
		user_roles = frappe.get_roles(frappe.session.user)
		if "Customer" not in user_roles or len(user_roles) > 1:
			is_staff = True
	
	if not is_staff:
		frappe.throw(_("Only staff members can save payment information"), frappe.PermissionError)
	
	# Validate payment type
	if payment_type not in ["first", "second"]:
		frappe.throw(_("Invalid payment type. Must be 'first' or 'second'"))
	
	# Update payment information based on type
	if payment_type == "first":
		if amount:
			clearance.amount = flt(amount)
		if branch:
			clearance.first_payment_branch = branch
		if account_number:
			clearance.first_payment_account_number = account_number
		if custom_id_code:
			clearance.first_payment_custom_id_code = custom_id_code
	elif payment_type == "second":
		if amount:
			clearance.additional_payment_amount = flt(amount)
		if branch:
			clearance.second_payment_branch = branch
		if account_number:
			clearance.second_payment_account_number = account_number
		if custom_id_code:
			clearance.second_payment_custom_id_code = custom_id_code
	
	# Save the document
	clearance.save()
	frappe.db.commit()
	
	# Create notification for customer
	try:
		# Get customer user
		customer_user = None
		portal_users = frappe.get_all(
			"Portal User",
			filters={"parent": clearance.customer, "parenttype": "Customer"},
			fields=["user"],
			limit=1
		)
		if portal_users:
			customer_user = portal_users[0].user
		else:
			# Try to get from Contact
			contacts = frappe.get_all(
				"Contact",
				filters={"link_doctype": "Customer", "link_name": clearance.customer},
				fields=["name"]
			)
			if contacts:
				contact_doc = frappe.get_doc("Contact", contacts[0].name)
				if contact_doc.email:
					customer_user = frappe.db.get_value("User", {"email": contact_doc.email}, "name")
		
		if customer_user:
			payment_label = _("First Payment") if payment_type == "first" else _("Additional Payment")
			notification_doc = frappe.get_doc({
				"doctype": "Notification Log",
				"for_user": customer_user,
				"type": "Alert",
				"document_type": "Custom Clearance",
				"document_name": clearance_name,
				"subject": _("Payment Information Updated - {0}").format(clearance_name),
				"email_content": _("{0} information has been updated for your Custom Clearance {1}. Please check the payment details on the portal.").format(
					payment_label, clearance_name
				)
			})
			notification_doc.insert(ignore_permissions=True)
			frappe.db.commit()
	except Exception as e:
		# Log error but don't fail the save
		frappe.log_error(f"Error creating notification: {str(e)}", "Payment Info Notification Error")
	
	return {"success": True, "message": _("Payment information saved successfully")}


@frappe.whitelist()
def send_payment_notification(clearance_name, payment_row_name, payment_type, amount, branch=None, account_number=None, custom_id_code=None):
	"""Create Todo for payment notification"""
	import traceback
	frappe.log_error(f"=== send_payment_notification called ===\nClearance: {clearance_name}\nPayment Row: {payment_row_name}\nType: {payment_type}\nAmount: {amount}\nUser: {frappe.session.user}", "Payment Notification Debug")
	
	if frappe.session.user == "Guest":
		frappe.log_error("ERROR: Guest user attempted to send notification", "Payment Notification Debug")
		frappe.throw(_("Please login to send notifications"), frappe.PermissionError)
	
	# Get the custom clearance document
	try:
		clearance = frappe.get_doc("Custom Clearance", clearance_name)
		frappe.log_error(f"Clearance document loaded: {clearance.name}", "Payment Notification Debug")
	except Exception as e:
		frappe.log_error(f"ERROR loading clearance: {str(e)}\n{traceback.format_exc()}", "Payment Notification Debug")
		raise
	
	# Check if user is staff/admin
	is_staff = False
	if frappe.session.user == "Administrator":
		is_staff = True
	else:
		user_roles = frappe.get_roles(frappe.session.user)
		if "Customer" not in user_roles or len(user_roles) > 1:
			is_staff = True
	
	if not is_staff:
		frappe.throw(_("Only staff members can send payment notifications"), frappe.PermissionError)
	
	# Get customer user
	customer_user = None
	portal_users = frappe.get_all(
		"Portal User",
		filters={"parent": clearance.customer, "parenttype": "Customer"},
		fields=["user"],
		limit=1
	)
	if portal_users:
		customer_user = portal_users[0].user
	else:
		# Try to get from Contact
		contacts = frappe.get_all(
			"Contact",
			filters={"link_doctype": "Customer", "link_name": clearance.customer},
			fields=["name"]
		)
		if contacts:
			contact_doc = frappe.get_doc("Contact", contacts[0].name)
			if contact_doc.email:
				customer_user = frappe.db.get_value("User", {"email": contact_doc.email}, "name")
	
	if not customer_user:
		frappe.log_error(f"ERROR: Customer user not found for customer: {clearance.customer}", "Payment Notification Debug")
		frappe.throw(_("Customer user not found. Cannot create todo."))
	
	frappe.log_error(f"Customer user found: {customer_user}", "Payment Notification Debug")
	
	# Build description message
	payment_label = _("First Payment") if payment_type == "First Payment" else _("Additional Payment")
	description_parts = [
		_("Please make a payment for your Custom Clearance: {0}").format(clearance_name),
		"",
		_("Payment Type: {0}").format(payment_label),
		_("Amount to Pay: {0}").format(frappe.format(flt(amount), {"fieldtype": "Currency"}))
	]
	
	if branch:
		description_parts.append(_("Bank Branch: {0}").format(branch))
	if account_number:
		description_parts.append(_("Account Number: {0}").format(account_number))
	if custom_id_code:
		description_parts.append(_("Custom ID Code: {0}").format(custom_id_code))
	
	description_parts.extend([
		"",
		_("Please transfer the amount to the specified bank account and upload the payment receipt on the portal."),
		_("After payment, you can upload the receipt in the payment section.")
	])
	
	description = "\n".join(description_parts)
	frappe.log_error(f"Todo description prepared: {description[:200]}...", "Payment Notification Debug")
	
	# Create Todo
	try:
		frappe.log_error("Creating Todo document...", "Payment Notification Debug")
		todo_doc = frappe.get_doc({
			"doctype": "ToDo",
			"allocated_to": customer_user,
			"description": description,
			"reference_type": "Custom Clearance",
			"reference_name": clearance_name,
			"priority": "High",
			"status": "Open"
		})
		todo_doc.insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.log_error(f"SUCCESS: Todo created: {todo_doc.name}", "Payment Notification Debug")
		
		return {"success": True, "message": _("Todo created successfully"), "todo_name": todo_doc.name}
	except Exception as e:
		frappe.log_error(f"ERROR creating payment todo: {str(e)}\n{traceback.format_exc()}", "Payment Todo Error")
		frappe.throw(_("Error creating todo: {0}").format(str(e)))


@frappe.whitelist()
def update_payment_receipt(clearance_name, payment_row_name, file_url):
	"""Update payment receipt attachment"""
	import traceback
	frappe.log_error(f"=== update_payment_receipt called ===\nClearance: {clearance_name}\nPayment Row: {payment_row_name}\nFile URL: {file_url}\nUser: {frappe.session.user}", "Payment Receipt Upload Debug")
	
	if frappe.session.user == "Guest":
		frappe.log_error("ERROR: Guest user attempted to upload receipt", "Payment Receipt Upload Debug")
		frappe.throw(_("Please login to upload payment receipt"), frappe.PermissionError)
	
	# Get the custom clearance document
	try:
		clearance = frappe.get_doc("Custom Clearance", clearance_name)
		frappe.log_error(f"Clearance document loaded: {clearance.name}", "Payment Receipt Upload Debug")
	except Exception as e:
		frappe.log_error(f"ERROR loading clearance: {str(e)}\n{traceback.format_exc()}", "Payment Receipt Upload Debug")
		raise
	
	# Check permissions - user must be linked to the customer
	if frappe.session.user != "Administrator":
		customer = None
		contact = frappe.db.get_value("Contact", {"user": frappe.session.user}, "name")
		if contact:
			contact_doc = frappe.get_doc("Contact", contact)
			for link in contact_doc.links:
				if link.link_doctype == "Customer":
					customer = link.link_name
					break
		
		if not customer:
			portal_users = frappe.get_all(
				"Portal User",
				filters={"user": frappe.session.user, "parenttype": "Customer"},
				fields=["parent"],
				limit=1
			)
			if portal_users:
				customer = portal_users[0].parent
		
		if not customer or clearance.customer != customer:
			frappe.throw(_("You don't have permission to upload payment receipt for this Custom Clearance"), frappe.PermissionError)
	
	# Find the payment row and update attachment
	frappe.log_error(f"Looking for payment row: {payment_row_name}\nTotal payments: {len(clearance.payments) if clearance.payments else 0}", "Payment Receipt Upload Debug")
	payment_updated = False
	if clearance.payments:
		for payment in clearance.payments:
			frappe.log_error(f"Checking payment: {payment.name} == {payment_row_name}", "Payment Receipt Upload Debug")
			if payment.name == payment_row_name:
				payment.attachment = file_url
				payment_updated = True
				frappe.log_error(f"Payment row found and updated", "Payment Receipt Upload Debug")
				break
	
	if not payment_updated:
		frappe.log_error(f"ERROR: Payment row not found: {payment_row_name}", "Payment Receipt Upload Debug")
		frappe.throw(_("Payment row not found"))
	
	# Save the document
	try:
		frappe.log_error("Saving clearance document...", "Payment Receipt Upload Debug")
		clearance.save()
		frappe.db.commit()
		frappe.log_error("SUCCESS: Payment receipt updated", "Payment Receipt Upload Debug")
		return {"success": True, "message": _("Payment receipt updated successfully")}
	except Exception as e:
		frappe.log_error(f"ERROR saving document: {str(e)}\n{traceback.format_exc()}", "Payment Receipt Upload Debug")
		raise
