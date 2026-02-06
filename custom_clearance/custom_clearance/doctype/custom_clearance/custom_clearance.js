// Copyright (c) 2026, Custom Clearance and Contributors
// License: MIT. See license.txt

frappe.ui.form.on("Custom Clearance", {
	refresh: function(frm) {
		// Set query for template based on shipping type
		if (frm.doc.shipping_type) {
			frm.set_query("template", function() {
				return {
					filters: {
						shipping_type: frm.doc.shipping_type,
						is_active: 1
					}
				};
			});
		}
		
		// Add Create Sales Invoice button - show when status is Yellow or Red (payment required)
		if (!frm.is_new() && !frm.doc.sales_invoice && frm.doc.amount && frm.doc.status in ["Yellow", "Red"]) {
			frm.add_custom_button(__("Create Sales Invoice"), function() {
				frappe.call({
					method: "custom_clearance.custom_clearance.doctype.custom_clearance.custom_clearance.create_sales_invoice",
					args: {
						source_name: frm.doc.name
					},
					callback: function(r) {
						if (r.message && r.message.invoice_name) {
							// Redirect to the sales invoice page
							frappe.set_route("Form", "Sales Invoice", r.message.invoice_name);
						}
					}
				});
			}, __("Create"));
		}
		
		// Show Sales Invoice link if exists
		if (frm.doc.sales_invoice) {
			frm.add_custom_button(__("View Sales Invoice"), function() {
				frappe.set_route("Form", "Sales Invoice", frm.doc.sales_invoice);
			}, __("View"));
		}
	},

	shipping_type: function(frm) {
		// Clear template when shipping type changes
		if (frm.doc.template) {
			frm.set_value("template", "");
			frm.clear_table("required_documents");
			frm.refresh_field("required_documents");
		}
	},

	template: function(frm) {
		// When template is selected, populate the child table
		if (frm.doc.template) {
			frappe.call({
				method: "custom_clearance.custom_clearance.doctype.custom_clearance.custom_clearance.get_template_documents",
				args: {
					template: frm.doc.template
				},
				callback: function(r) {
					if (r.message) {
						// Clear existing rows
						frm.clear_table("required_documents");
						
						// Add documents from template
						r.message.forEach(function(doc) {
							let row = frm.add_child("required_documents");
							row.document_name = doc.document_name;
							row.is_required = doc.is_required;
							row.has_sub_items = doc.has_sub_items;
							row.sub_items = doc.sub_items;
						});
						
						frm.refresh_field("required_documents");
					}
				}
			});
		} else {
			// Clear table if template is removed
			frm.clear_table("required_documents");
			frm.refresh_field("required_documents");
		}
	}
});




frappe.ui.form.on('Custom Clearance Payment', {
	refresh: function(frm) {
		console.log('=== Custom Clearance Form Refresh ===');
		console.log('Form name:', frm.doc.name);
		console.log('Payments field exists:', !!frm.fields_dict.payments);
		
		// Handle button clicks in payments grid
		if (frm.fields_dict.payments && frm.fields_dict.payments.grid) {
			console.log('Payments grid found, setting up button handlers...');
			
			// Set up click handler for button field in grid
			frm.fields_dict.payments.grid.wrapper.on('click', '[data-fieldname="send_notification"]', function() {
				console.log('=== Send Notification Button Clicked in Grid ===');
				const $row = $(this).closest('.grid-row');
				const row_name = $row.attr('data-name');
				console.log('Row name:', row_name);
				
				if (!row_name) {
					console.error('ERROR: Row name not found');
					return;
				}
				
				// Get row data
				const row_doc = frm.fields_dict.payments.grid.get_row_by_name(row_name);
				if (!row_doc) {
					console.error('ERROR: Row doc not found');
					return;
				}
				
				const row = row_doc.doc;
				console.log('Payment row data:', row);
				
				if (!row.payment_type || !row.amount) {
					console.log('ERROR: Payment Type or Amount missing');
					frappe.msgprint(__('Please fill Payment Type and Amount before sending notification'));
					return;
				}
				
				const args = {
					clearance_name: frm.doc.name,
					payment_row_name: row.name,
					payment_type: row.payment_type,
					amount: row.amount,
					branch: row.branch || null,
					account_number: row.account_number || null,
					custom_id_code: row.custom_id_code || null
				};
				
				console.log('Calling send_payment_notification with args:', JSON.stringify(args, null, 2));
				
				frappe.call({
					method: 'custom_clearance.custom_clearance.doctype.custom_clearance.custom_clearance.send_payment_notification',
					args: args,
					callback: function(r) {
						console.log('=== Response from send_payment_notification ===');
						console.log('Full response:', JSON.stringify(r, null, 2));
						if (r.message && r.message.success) {
							console.log('SUCCESS: Todo created:', r.message.todo_name);
							frappe.show_alert({
								message: __('Todo created successfully'),
								indicator: 'green'
							}, 3);
						} else {
							console.error('ERROR: Failed to create todo. Response:', r.message);
							frappe.show_alert({
								message: r.message && r.message.message ? r.message.message : __('Error creating todo'),
								indicator: 'red'
							}, 5);
						}
					},
					error: function(r) {
						console.error('=== ERROR: API call failed ===');
						console.error('Error response:', JSON.stringify(r, null, 2));
						frappe.show_alert({
							message: __('Error creating todo. Please check console for details.'),
							indicator: 'red'
						}, 5);
					}
				});
			});
		} else {
			console.log('WARNING: Payments grid not found');
		}
	}
});

// Handle button field click in child table (alternative method)
frappe.ui.form.on('Custom Clearance Payment', {
	send_notification: function(frm, cdt, cdn) {
		console.log('=== Send Notification Handler Triggered (Alternative Method) ===');
		console.log('cdt:', cdt, 'cdn:', cdn);
		let row = locals[cdt][cdn];
		console.log('Payment row data:', row);
		
		if (!row) {
			console.error('ERROR: Row data not found');
			return;
		}
		
		if (!row.payment_type || !row.amount) {
			console.log('ERROR: Payment Type or Amount missing');
			frappe.msgprint(__('Please fill Payment Type and Amount before sending notification'));
			return;
		}
		
		const args = {
			clearance_name: frm.doc.name,
			payment_row_name: row.name,
			payment_type: row.payment_type,
			amount: row.amount,
			branch: row.branch || null,
			account_number: row.account_number || null,
			custom_id_code: row.custom_id_code || null
		};
		
		console.log('Calling send_payment_notification with args:', JSON.stringify(args, null, 2));
		
		frappe.call({
			method: 'custom_clearance.custom_clearance.doctype.custom_clearance.custom_clearance.send_payment_notification',
			args: args,
			callback: function(r) {
				console.log('=== Response from send_payment_notification ===');
				console.log('Full response:', JSON.stringify(r, null, 2));
				if (r.message && r.message.success) {
					console.log('SUCCESS: Todo created:', r.message.todo_name);
					frappe.show_alert({
						message: __('Todo created successfully'),
						indicator: 'green'
					}, 3);
				} else {
					console.error('ERROR: Failed to create todo. Response:', r.message);
					frappe.show_alert({
						message: r.message && r.message.message ? r.message.message : __('Error creating todo'),
						indicator: 'red'
					}, 5);
				}
			},
			error: function(r) {
				console.error('=== ERROR: API call failed ===');
				console.error('Error response:', JSON.stringify(r, null, 2));
				frappe.show_alert({
					message: __('Error creating todo. Please check console for details.'),
					indicator: 'red'
				}, 5);
			}
		});
	}
});
