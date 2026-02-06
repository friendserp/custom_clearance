# Copyright (c) 2026, Custom Clearance and Contributors
# License: MIT. See license.txt

import frappe
from frappe import _


def get_context(context):
	"""Get context for custom clearances portal page"""
	# Check if user is logged in
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/custom_clearances"
		frappe.local.response["type"] = "redirect"
		raise frappe.Redirect
	
	# Check if this is a detail page (has a name in the path)
	path_parts = frappe.local.request.path.strip("/").split("/")
	clearance_name = None
	
	if "custom_clearances" in path_parts:
		idx = path_parts.index("custom_clearances")
		if idx + 1 < len(path_parts):
			potential_name = path_parts[idx + 1]
			# Check if it's a valid clearance name (not empty and not another route segment)
			if potential_name and potential_name not in ["", "index", "list"]:
				# Verify it's actually a clearance name by checking if it exists
				if frappe.db.exists("Custom Clearance", potential_name):
					clearance_name = potential_name
					# This is a detail page
					return get_detail_context(context, clearance_name)
	
	# This is the list page
	return get_list_context(context)


def get_list_context(context):
	"""Get context for custom clearances list page"""
	# Get customer linked to the current user
	customer = None
	customer_lookup_method = None
	try:
		if frappe.session.user != "Administrator":
			# Try to get customer from Contact
			contact = frappe.db.get_value("Contact", {"user": frappe.session.user}, "name")
			if contact:
				contact_doc = frappe.get_doc("Contact", contact)
				# Get customer from contact links
				for link in contact_doc.links:
					if link.link_doctype == "Customer":
						customer = link.link_name
						customer_lookup_method = "Contact"
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
					customer_lookup_method = "Portal User"
			
			# Log customer lookup result (always)
			frappe.log_error(
				f"Custom Clearance Portal - Customer Lookup\n"
				f"User: {frappe.session.user}\n"
				f"Customer found: {customer or 'None'}\n"
				f"Lookup method: {customer_lookup_method or 'None'}\n"
				f"User roles: {frappe.get_roles()}",
				"Custom Clearance Portal - Customer Lookup"
			)
		else:
			# Log admin access
			frappe.log_error(
				f"Custom Clearance Portal - Customer Lookup\n"
				f"User: {frappe.session.user} (Administrator)\n"
				f"Customer: None (showing all clearances)",
				"Custom Clearance Portal - Customer Lookup"
			)
	except Exception as e:
		import traceback
		frappe.log_error(
			f"Error finding customer for user: {frappe.session.user}\nError: {str(e)}\nTraceback: {traceback.format_exc()}",
			"Custom Clearance Portal - Customer Lookup Error"
		)
	
	# If no customer found, show empty list or throw error
	if not customer and frappe.session.user != "Administrator":
		frappe.log_error(
			f"No customer found for user: {frappe.session.user}\nUser roles: {frappe.get_roles()}",
			"Custom Clearance Portal - No Customer Found"
		)
		context.custom_clearances = []
		context.no_customer = True
		context.message = _("No customer account found. Please contact administrator.")
		return context
	
	# Fetch custom clearances
	filters = {}
	if customer:
		filters["customer"] = customer
	
	# Get custom clearances - use direct SQL for portal users to avoid permission issues
	try:
		if customer:
			# Get customer name to match against (in case Custom Clearance stores names instead of IDs)
			customer_name = frappe.db.get_value("Customer", customer, "customer_name")
			
			# Use direct SQL query - check both customer ID and customer name
			# This handles cases where Custom Clearance might store customer names instead of IDs
			context.custom_clearances = frappe.db.sql("""
				SELECT 
					name,
					customer,
					clearance_date,
					shipping_type,
					status,
					risk_result,
					amount,
					payment_status,
					payment_date,
					sales_invoice,
					creation,
					modified
				FROM `tabCustom Clearance`
				WHERE customer = %s OR customer = %s
				ORDER BY creation DESC
			""", (customer, customer_name), as_dict=True)
			
			# Always log query execution details
			result_count = len(context.custom_clearances)
			
			# Check if records exist for this customer in database (by ID and name)
			total_count_result = frappe.db.sql("""
				SELECT COUNT(*) as count 
				FROM `tabCustom Clearance` 
				WHERE customer = %s OR customer = %s
			""", (customer, customer_name), as_dict=True)
			total_count = total_count_result[0]['count'] if total_count_result else 0
			
			# Get sample clearance names for logging
			sample_names = []
			if context.custom_clearances:
				sample_names = [c['name'] for c in context.custom_clearances[:5]]
			
			# Log query execution details (always)
			frappe.log_error(
				f"Custom Clearance Portal Query Execution\n"
				f"User: {frappe.session.user}\n"
				f"Customer ID: {customer}\n"
				f"Customer Name: {customer_name}\n"
				f"Query returned: {result_count} results\n"
				f"Total records in DB for customer (ID or Name): {total_count}\n"
				f"User roles: {frappe.get_roles()}\n"
				f"Has read permission: {frappe.has_permission('Custom Clearance', 'read')}\n"
				f"Sample clearance names: {sample_names if sample_names else 'None'}\n"
				f"Status: {'SUCCESS' if result_count > 0 else 'EMPTY RESULTS' if total_count == 0 else 'PERMISSION ISSUE (records exist but query returned empty)'}",
				"Custom Clearance Portal - Query Execution"
			)
		else:
			# Administrator or no customer - use frappe.get_list
			context.custom_clearances = frappe.get_list(
				"Custom Clearance",
				filters=filters,
				fields=[
					"name",
					"customer",
					"clearance_date",
					"shipping_type",
					"status",
					"risk_result",
					"amount",
					"payment_status",
					"payment_date",
					"sales_invoice",
					"creation",
					"modified"
				],
				order_by="creation desc"
			)
			
			# Log admin query execution
			frappe.log_error(
				f"Custom Clearance Portal Query Execution (Admin)\n"
				f"User: {frappe.session.user}\n"
				f"Filters: {filters}\n"
				f"Query returned: {len(context.custom_clearances)} results\n"
				f"User roles: {frappe.get_roles()}",
				"Custom Clearance Portal - Query Execution"
			)
			
	except Exception as e:
		import traceback
		frappe.log_error(
			f"Error fetching custom clearances list\n"
			f"Error: {str(e)}\n"
			f"Filters: {filters}\n"
			f"User: {frappe.session.user}\n"
			f"Customer: {customer}\n"
			f"User roles: {frappe.get_roles()}\n"
			f"Traceback: {traceback.format_exc()}",
			"Custom Clearance Portal - Query Error"
		)
		# Fallback to empty list
		context.custom_clearances = []
	
	# Get customer name for display and set customer in context
	if customer:
		customer_name_value = frappe.db.get_value("Customer", customer, "customer_name")
		context.customer_name = customer_name_value or customer
		context.customer = customer  # Add customer ID to context for template
	else:
		context.customer_name = None
		context.customer = None  # Set to None if no customer
	
	context.no_cache = 1
	context.parents = [{"name": _("My Account"), "route": "/me"}]
	context.title = _("Custom Clearances")
	context.is_list = True
	
	return context


def get_detail_context(context, clearance_name):
	"""Get context for custom clearance detail page"""
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
	context.clearance = clearance
	context.doc = clearance
	
	# Get customer name
	if clearance.customer:
		context.customer_name = frappe.db.get_value("Customer", clearance.customer, "customer_name") or clearance.customer
	
	# Get required documents
	context.required_documents = []
	if clearance.required_documents:
		for doc in clearance.required_documents:
			doc_dict = doc.as_dict()
			# Get file info if attachment exists
			if doc.attachment:
				file_doc = frappe.db.get_value("File", {"file_url": doc.attachment}, ["file_name", "file_size"], as_dict=True)
				if file_doc:
					doc_dict["file_info"] = file_doc
			# Include status and reason for declined documents
			doc_dict["status"] = doc.status if hasattr(doc, 'status') else None
			doc_dict["reason"] = doc.reason if hasattr(doc, 'reason') else None
			context.required_documents.append(doc_dict)
	
	context.no_cache = 1
	context.parents = [
		{"name": _("My Account"), "route": "/me"},
		{"name": _("Custom Clearances"), "route": "/custom_clearances"}
	]
	context.title = clearance.name
	context.is_detail = True
	
	return context
