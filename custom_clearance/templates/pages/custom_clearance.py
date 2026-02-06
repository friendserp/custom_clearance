# Copyright (c) 2026, Custom Clearance and Contributors
# License: MIT. See license.txt

import frappe
from frappe import _


def get_context(context):
	"""Get context for custom clearance detail page"""
	context.no_cache = 1
	context.show_sidebar = True
	
	# Check if user is logged in
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/custom_clearances"
		frappe.local.response["type"] = "redirect"
		raise frappe.Redirect
	
	# Get clearance name from form_dict (set by Frappe's router via website_route_rules)
	clearance_name = frappe.form_dict.name
	
	if not clearance_name:
		frappe.throw(_("Custom Clearance not found"), frappe.DoesNotExistError)
	
	# Get the custom clearance document
	try:
		clearance = frappe.get_doc("Custom Clearance", clearance_name)
	except frappe.DoesNotExistError:
		frappe.throw(_("Custom Clearance not found"), frappe.DoesNotExistError)
	
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
		
		# Check if user has permission to view this clearance
		if not customer or clearance.customer != customer:
			frappe.throw(_("You don't have permission to view this Custom Clearance"), frappe.PermissionError)
	
	# Load the document with all details
	context.doc = clearance
	context.clearance = clearance
	
	# Get customer name
	if clearance.customer:
		context.customer_name = frappe.db.get_value("Customer", clearance.customer, "customer_name") or clearance.customer
	
	# Get payments from child table - query directly to ensure we get the data
	context.payments = []
	try:
		# Query the child table directly
		payment_rows = frappe.get_all(
			"Custom Clearance Payment",
			filters={"parent": clearance_name},
			fields=["name", "payment_type", "amount", "branch", "account_number", "custom_id_code", "attachment"],
			order_by="idx asc"
		)
		context.payments = payment_rows
	except Exception as e:
		# If there's an error accessing payments, log it but continue
		frappe.log_error(f"Error loading payments: {str(e)}", "Payment Loading Error")
		context.payments = []
	
	# Also add payments to clearance object for template access
	clearance.payments = context.payments
	
	# Get required documents
	context.required_documents = []
	if clearance.required_documents:
		for doc in clearance.required_documents:
			doc_dict = doc.as_dict()
			# Include the row name (id) for updating
			doc_dict["row_name"] = doc.name
			# Get file info if attachment exists
			if doc.attachment:
				file_doc = frappe.db.get_value("File", {"file_url": doc.attachment}, ["file_name", "file_size"], as_dict=True)
				if file_doc:
					doc_dict["file_info"] = file_doc
			# Include status and reason for declined documents
			doc_dict["status"] = doc.status if hasattr(doc, 'status') else None
			doc_dict["reason"] = doc.reason if hasattr(doc, 'reason') else None
			context.required_documents.append(doc_dict)
	
	# Get comments
	context.comments = []
	comments = frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": "Custom Clearance",
			"reference_name": clearance_name,
			"comment_type": "Comment",
		},
		fields=["name", "content", "comment_by", "comment_email", "creation", "owner"],
		order_by="creation asc"
	)
	
	# Check if current user is a customer (guest)
	is_guest_user = False
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
		
		if customer and clearance.customer == customer:
			is_guest_user = True
	
	context.is_guest_user = is_guest_user
	
	# Check if user is staff/admin (can change statuses)
	# Staff/admin = not a customer, or Administrator
	context.is_staff = False
	if frappe.session.user == "Administrator":
		context.is_staff = True
	else:
		# Check if user has roles other than Customer
		user_roles = frappe.get_roles(frappe.session.user)
		if "Customer" not in user_roles or len(user_roles) > 1:
			context.is_staff = True
	
	# Get current user for comparison
	current_user = frappe.session.user
	
	# Get current user's customer (if any)
	current_user_customer = None
	if current_user != "Administrator":
		contact = frappe.db.get_value("Contact", {"user": current_user}, "name")
		if contact:
			contact_doc = frappe.get_doc("Contact", contact)
			for link in contact_doc.links:
				if link.link_doctype == "Customer":
					current_user_customer = link.link_name
					break
		
		if not current_user_customer:
			portal_users = frappe.get_all(
				"Portal User",
				filters={"user": current_user, "parenttype": "Customer"},
				fields=["parent"],
				limit=1
			)
			if portal_users:
				current_user_customer = portal_users[0].parent
	
	for comment in comments:
		comment_dict = {
			"name": comment.name,
			"content": comment.content,
			"comment_by": comment.comment_by or comment.comment_email,
			"comment_email": comment.comment_email,
			"creation": comment.creation,
			"owner": comment.owner
		}
		
		# Check if comment is from current user (for positioning)
		is_current_user = (comment.owner == current_user or comment.comment_email == current_user)
		comment_dict["is_current_user"] = is_current_user
		
		# Determine display name: "You" for current customer, "Admin" for others
		comment_customer = None
		if comment.owner != "Administrator":
			contact = frappe.db.get_value("Contact", {"user": comment.owner}, "name")
			if contact:
				contact_doc = frappe.get_doc("Contact", contact)
				for link in contact_doc.links:
					if link.link_doctype == "Customer":
						comment_customer = link.link_name
						break
			
			if not comment_customer:
				portal_users = frappe.get_all(
					"Portal User",
					filters={"user": comment.owner, "parenttype": "Customer"},
					fields=["parent"],
					limit=1
				)
				if portal_users:
					comment_customer = portal_users[0].parent
		
		# Set display name
		if comment_customer and comment_customer == current_user_customer and comment_customer == clearance.customer:
			comment_dict["display_name"] = _("You")
		else:
			comment_dict["display_name"] = _("Admin")
		
		# Also keep is_customer for reference
		is_customer = False
		if comment_customer and comment_customer == clearance.customer:
			is_customer = True
		
		comment_dict["is_customer"] = is_customer
		context.comments.append(comment_dict)
	
	context.parents = frappe.form_dict.parents or [
		{"name": _("My Account"), "route": "/me"},
		{"name": _("Custom Clearances"), "route": "/custom_clearances"}
	]
	context.title = clearance.name
	
	return context
