# Copyright (c) 2026, Custom Clearance and Contributors
# License: MIT. See license.txt

import frappe


def create_service_item():
	"""Create Custom Clearance Service Item"""
	if not frappe.db.exists("Item", "Custom Clearance Service"):
		# Try to get Services item group, if not exists, use All Item Groups
		item_group = frappe.db.get_value("Item Group", "Services", "name")
		if not item_group:
			# Try to get any non-group item group
			item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
			if not item_group:
				# Use All Item Groups as fallback
				item_group = "All Item Groups"
		
		service_item = frappe.get_doc({
			"doctype": "Item",
			"item_code": "Custom Clearance Service",
			"item_name": "Custom Clearance Service",
			"item_group": item_group,
			"is_stock_item": 0,
			"is_sales_item": 1,
			"is_service_item": 1,
			"description": "Custom Clearance Service for import/export clearance"
		})
		service_item.insert(ignore_permissions=True)
		frappe.db.commit()


def create_default_templates():
	"""Create default templates for Air and Sea shipping"""
	
	# Sea Shipping Template
	sea_documents = [
		{"document_name": "Commercial Invoice", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Packing List", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Bill of Lading", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Certificate of Origin", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Bank Permit", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Payment Receipt / Invoice", "is_required": 1, "has_sub_items": 0},
		{"document_name": "License", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Agreement", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Settlement of Freight", "is_required": 1, "has_sub_items": 1, "sub_items": "Inland, Other cost, External"},
		{"document_name": "Analysis Certificate", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Health Certificate", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Insurance", "is_required": 1, "has_sub_items": 1, "sub_items": "Marine Insurance, Insurance Receipt"},
	]
	
	# Air Shipping Template (similar but may have different requirements)
	air_documents = [
		{"document_name": "Commercial Invoice", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Packing List", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Air Waybill", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Certificate of Origin", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Bank Permit", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Payment Receipt / Invoice", "is_required": 1, "has_sub_items": 0},
		{"document_name": "License", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Agreement", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Analysis Certificate", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Health Certificate", "is_required": 1, "has_sub_items": 0},
		{"document_name": "Insurance", "is_required": 1, "has_sub_items": 1, "sub_items": "Marine Insurance, Insurance Receipt"},
	]
	
	# Create Sea Template
	if not frappe.db.exists("Custom Clearance Template", "Sea Shipping Template"):
		sea_template = frappe.get_doc({
			"doctype": "Custom Clearance Template",
			"template_name": "Sea Shipping Template",
			"shipping_type": "Sea",
			"is_active": 1,
			"description": "Default template for sea shipping imports with all required documents"
		})
		
		for doc in sea_documents:
			sea_template.append("required_documents", doc)
		
		sea_template.insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.msgprint("Created Sea Shipping Template")
	
	# Create Air Template
	if not frappe.db.exists("Custom Clearance Template", "Air Shipping Template"):
		air_template = frappe.get_doc({
			"doctype": "Custom Clearance Template",
			"template_name": "Air Shipping Template",
			"shipping_type": "Air",
			"is_active": 1,
			"description": "Default template for air shipping imports with all required documents"
		})
		
		for doc in air_documents:
			air_template.append("required_documents", doc)
		
		air_template.insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.msgprint("Created Air Shipping Template")


def after_install():
	"""Run after app installation"""
	create_service_item()
	create_default_templates()