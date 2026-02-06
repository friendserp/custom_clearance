# Copyright (c) 2026, Custom Clearance and Contributors
# License: MIT. See license.txt

import frappe


def create_custom_clearance_workflow():
	"""Create workflow for Custom Clearance"""
	
	# Create Workflow States
	states = [
		{"workflow_state_name": "Draft", "icon": "question-sign", "style": "Inverse"},
		{"workflow_state_name": "Documents Pending", "icon": "file", "style": "Warning"},
		{"workflow_state_name": "Documents Submitted", "icon": "ok-sign", "style": "Info"},
		{"workflow_state_name": "Under Customs Review", "icon": "search", "style": "Warning"},
		{"workflow_state_name": "Payment Pending", "icon": "ok-sign", "style": "Warning"},
		{"workflow_state_name": "Cleared", "icon": "ok", "style": "Success"},
		{"workflow_state_name": "Closed", "icon": "remove", "style": "Inverse"},
	]
	
	for state_data in states:
		if not frappe.db.exists("Workflow State", state_data["workflow_state_name"]):
			state_doc = frappe.get_doc({
				"doctype": "Workflow State",
				**state_data
			})
			state_doc.insert(ignore_permissions=True)
		frappe.db.commit()
	
	# Create Workflow Actions
	actions = [
		"Submit Documents",
		"Send for Customs Review",
		"Mark Payment Pending",
		"Mark Cleared",
		"Close",
		"Reopen",
	]
	
	for action_name in actions:
		if not frappe.db.exists("Workflow Action Master", action_name):
			action_doc = frappe.get_doc({
				"doctype": "Workflow Action Master",
				"workflow_action_name": action_name
			})
			action_doc.insert(ignore_permissions=True)
		frappe.db.commit()
	
	# Delete existing workflow if it exists to recreate it
	if frappe.db.exists("Workflow", "Custom Clearance Workflow"):
		frappe.delete_doc("Workflow", "Custom Clearance Workflow", force=1, ignore_permissions=True)
	
	workflow = frappe.new_doc("Workflow")
	workflow.workflow_name = "Custom Clearance Workflow"
	workflow.document_type = "Custom Clearance"
	workflow.workflow_state_field = "workflow_state"
	workflow.is_active = 1
	workflow.override_status = 1
	workflow.send_email_alert = 0
	
	# Add States
	workflow.append("states", {
		"state": "Draft",
		"doc_status": 0,
		"allow_edit": "System Manager",
		"is_optional_state": 0,
		"send_email": 0
	})
	workflow.append("states", {
		"state": "Documents Pending",
		"doc_status": 0,
		"allow_edit": "System Manager",
		"is_optional_state": 0,
		"send_email": 0
	})
	workflow.append("states", {
		"state": "Documents Submitted",
		"doc_status": 0,
		"allow_edit": "System Manager",
		"is_optional_state": 0,
		"send_email": 0
	})
	workflow.append("states", {
		"state": "Under Customs Review",
		"doc_status": 0,
		"allow_edit": "System Manager",
		"is_optional_state": 0,
		"send_email": 0
	})
	workflow.append("states", {
		"state": "Payment Pending",
		"doc_status": 0,
		"allow_edit": "System Manager",
		"is_optional_state": 0,
		"send_email": 0
	})
	workflow.append("states", {
		"state": "Cleared",
		"doc_status": 1,
		"allow_edit": "System Manager",
		"is_optional_state": 0,
		"send_email": 0
	})
	workflow.append("states", {
		"state": "Closed",
		"doc_status": 2,
		"allow_edit": "System Manager",
		"is_optional_state": 0,
		"send_email": 0
	})
	
	# Add Transitions
	# Draft -> Documents Pending
	workflow.append("transitions", {
		"state": "Draft",
		"action": "Submit Documents",
		"next_state": "Documents Pending",
		"allowed": "System Manager",
		"allow_self_approval": 1,
		"condition": "doc.template and doc.required_documents"
	})
	
	# Documents Pending -> Documents Submitted (with validation)
	# Note: Validation is also done in the document's validate method
	workflow.append("transitions", {
		"state": "Documents Pending",
		"action": "Submit Documents",
		"next_state": "Documents Submitted",
		"allowed": "System Manager",
		"allow_self_approval": 1
	})
	
	# Documents Submitted -> Under Customs Review
	workflow.append("transitions", {
		"state": "Documents Submitted",
		"action": "Send for Customs Review",
		"next_state": "Under Customs Review",
		"allowed": "System Manager",
		"allow_self_approval": 1
	})
	
	# Under Customs Review -> Payment Pending
	workflow.append("transitions", {
		"state": "Under Customs Review",
		"action": "Mark Payment Pending",
		"next_state": "Payment Pending",
		"allowed": "System Manager",
		"allow_self_approval": 1
	})
	
	# Payment Pending -> Cleared
	workflow.append("transitions", {
		"state": "Payment Pending",
		"action": "Mark Cleared",
		"next_state": "Cleared",
		"allowed": "System Manager",
		"allow_self_approval": 1,
		"condition": "doc.payment_status == 'Paid'"
	})
	
	# Cleared -> Closed
	workflow.append("transitions", {
		"state": "Cleared",
		"action": "Close",
		"next_state": "Closed",
		"allowed": "System Manager",
		"allow_self_approval": 1
	})
	
	# Closed -> Cleared (Reopen)
	workflow.append("transitions", {
		"state": "Closed",
		"action": "Reopen",
		"next_state": "Cleared",
		"allowed": "System Manager",
		"allow_self_approval": 1
	})
	
	try:
		workflow.insert(ignore_permissions=True)
		frappe.db.commit()
		print("Custom Clearance Workflow created successfully!")
		if hasattr(frappe, 'msgprint'):
			frappe.msgprint("Custom Clearance Workflow created successfully!")
	except Exception as e:
		import traceback
		error_msg = f"Error creating Custom Clearance Workflow: {str(e)}\n{traceback.format_exc()}"
		frappe.log_error(error_msg, "Workflow Creation Error")
		print(error_msg)
		if hasattr(frappe, 'msgprint'):
			frappe.msgprint(f"Error creating workflow: {str(e)}", indicator="red")
		raise


@frappe.whitelist()
def create_workflow_manually():
	"""Manually create the Custom Clearance workflow - can be called from console or API"""
	try:
		create_custom_clearance_workflow()
		return {"status": "success", "message": "Workflow created successfully"}
	except Exception as e:
		return {"status": "error", "message": str(e)}
