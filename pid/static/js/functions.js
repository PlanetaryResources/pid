
/**
 * Rotate spacecraft in navbar, depends on jqueryrotate library
 */
$(".pri-a6-icon").rotate({
    bind:
    {
        mouseover: function () {
            $(this).rotate({animateTo: 360, duration: 30000})
        },
        mouseout: function () {
            $(this).rotate({animateTo: 0, duration: 1000})
        }
    }
});


/**
 * Delete an image
 * @param event The event causing the deletion, most likely button press
 * @param url The URL for the AJAX request to delete image
 */
function deleteImage(event, url) {
    var $parent = $(event.currentTarget).parent().parent();
    $.ajax({
        url: url,
        type: 'DELETE',
        success: function (result) {
            $parent.remove();
        }
    });
};


/**
 * Add bookmark for an object
 * @param user_id The PK (int) of the user bookmarking
 * @param bookmark_id The PK (int) of the object getting bookmarked
 * @param bookmark_class The class (str) of the object getting bookmarked
 */
function add_bookmark(user_id, bookmark_id, bookmark_class) {
    $.ajax({
        url: '/common/add_bookmark',
        type: 'POST',
        data: {
            user_id: user_id,
            bookmark_id: bookmark_id,
            bookmark_class: bookmark_class
        },
        success: function (result) {
            $('.pri-bookmark').removeClass('fa-bookmark-o');
            $('.pri-bookmark').addClass('fa-bookmark');
            $('.pri-bookmark').attr('title', 'Remove Bookmark').tooltip('fixTitle').tooltip('show');
        }
    });
};


/**
 * Remove bookmark for an object
 * @param user_id The PK (int) of the user un-bookmarking
 * @param bookmark_id The PK (int) of the object getting un-bookmarked
 * @param bookmark_class The class (str) of the object getting un-bookmarked
 */
function remove_bookmark(user_id, bookmark_id, bookmark_class) {
    $.ajax({
        url: '/common/remove_bookmark',
        type: 'POST',
        data: {
            user_id: user_id,
            bookmark_id: bookmark_id,
            bookmark_class: bookmark_class
        },
        success: function (result) {
            $('.pri-bookmark').removeClass('fa-bookmark');
            $('.pri-bookmark').addClass('fa-bookmark-o');
            $('.pri-bookmark').attr('title', 'Add Bookmark').tooltip('fixTitle').tooltip('show');
        }
    });
};


/**
 * Highlight an element, usually after update by an AJAX call
 * @param $e The element to highlight
 */
function highlight($e) {
    // TODO: Change to accept both element and string to element
    var bgColor = $e.css('background-color');
    $e.css('background-color', '#FFFF80');
    setTimeout(function () {
        if (bgColor === 'transparent') {
            bgColor = '';
        }
        $e.css('background-color', bgColor);
        $e.addClass('editable-bg-transition');
        setTimeout(function () {
            $e.removeClass('editable-bg-transition');
        }, 1700);
    }, 10);
}


/**
 * Pulse an element, depends on velocity library
 * @param $e The element to pulse
 */
function pulse($e) {
    $e.velocity({scale: 1.05}, {duration: 100}).velocity('reverse');
}

// For updating mass fields in GUI after something has happened on server, lets assume always on a part for now
// For instance: update_mass('#mass_fields_{{part_id}}', {{part_id}});
function update_mass(element_id, part_id) {
    $.ajax({
        url: '/part/update_mass',
        type: 'POST',
        data: {
            part_id: part_id
        },
        success: function (data) {
            $(element_id).html(data);
            update_parent_mass_fields(part_id);
        }
    });
}

function update_parent_mass_fields(part_component_id) {
    $('[data-part-component-part-id=' + part_component_id + ']').each(function () {
        var part_id = $(this).attr('data-part-component-parent-id');
        update_mass('#mass_fields_' + part_id, part_id);
    });
}

function reload_material_fields(part_id) {
    $.ajax({
        url: '/part/reload_material_fields',
        type: 'POST',
        data: {
            part_id: part_id
        },
        success: function (data) {
            $('#material_fields_' + part_id).html(data);
        }
    });
}

// A Javascript implementation of the flash functionality in Flask
function flash(message, category) {
    if (category == 'error') {
        var icon = 'icon-exclamation-sign';
        category = 'danger';
    }
    else if (category == 'success')
        var icon = 'icon-ok-sign';
    else
        var icon = 'icon-info-sign';
    $('<div class="row"><div class="col-md-12"><div class="alert alert-' + category + '"><a class="close" title="Close" data-dismiss="alert">&times;</a>' + message + '</div></div></div>').prependTo('div[role="main"]');
}

function downloadPSImage() {
    // If only one .pswp_img returned, download it. It's either thumbnail or only one in gallery.
    // Otherwise, grab index from window.href and download that one.
    var pswp_imgs = $('.pswp__img:visible');
    if (pswp_imgs.length == 0) return;
    else if (pswp_imgs.length == 1) {
        $("<a>").attr("href", pswp_imgs.attr('src'))[0].click();
    }
    else {
        var pid = window.location.href.split('=').slice(-1)[0];
        var img_wrap = $('.image-wrapper').find('.image-item-container')[pid - 1];
        var src = $(img_wrap).find('img').attr('src');
        $("<a>").attr("href", src)[0].click();
    }
}

function deleteReference(reference_id) {
    $.ajax({
        url: '/common/delete_reference',
        type: 'POST',
        data: {
            pk: reference_id
        },
        success: function (data) {
            $('#reference_' + reference_id).remove() // Remove row visually
            // Append empty row if no more references
            if ($('#ref-to-list tr').length == 0) {
                $('#ref-to-list').append('<tr class="no-references-to"><td colspan="4"><i>No references to anything.</i></td></tr>');
            }
            $.notify('Reference deleted');
        },
        error: function () {
            $.notify('Reference could not be deleted', {type: 'danger'});
        }
    });
}

function deleteProcedurePart(event, procedure_id, partId, partType) {
    $.ajax({
        url: '/procedure/remove_part',
        type: 'POST',
        data: {
            procedure_id: procedure_id,
            part_id: partId,
            part_type: partType
        },
        success: function (response) {
            $("#procedure-part-" + partType + "-" + partId).remove();
            if ($('#procedure-part-list').find('tr').length == 0) {
                $('#procedure-part-list').append('<tr class="no-parts-added"><td colspan="6"><i>No parts added.</i></td></tr>');
                $('#procedure-part-list').parent().find('thead').hide();
            }
            $.notify('Successfully removed part');
        }
    });
}

// Discrepancy related functions
function addDiscrepancy(e, parent_id, parent_class) {
    $(e).parents('table').find('.no-discrepancies-added').hide();
    $(e).parents('table').find('thead').show();
    var $parent = $(e).parents('table').find('tbody');
    var html = '<tr class="new-discrepancy"><td></td><td>';
    html += '<input type="text" class="form-control input-sm new-discrepancy-description" placeholder="Add description">';
    html += '</td><td>';
    html += '<select class="form-control input-sm new-discrepancy-disposition"><option value="None">---</option></select>';
    html += '</td><td>';
    html += '<input type="text" class="form-control input-sm new-discrepancy-justification" placeholder="Add justification">';
    html += '</td><td>';
    html += '<select class="form-control input-sm new-discrepancy-state"><option value="Open">Open</option><option value="Closed">Closed</option></select>';
    html += '</td><td width="100px">';
    html += '<div class="save-icon text-right"><div class="editable-buttons">';
    html += '<button type="submit" class="btn btn-primary btn-sm editable-submit" onclick="saveNewDiscrepancy(this, ' + parent_id + ', \'' + parent_class + '\')"><i class="glyphicon glyphicon-ok"></i></button>';
    html += '<button type="button" class="btn btn-default btn-sm editable-cancel" onclick="cancelNewDiscrepancy(this);"><i class="glyphicon glyphicon-remove"></i></button>';
    html += '</div></div></td></tr>';
    $parent.append(html);
    $.getJSON("/common/get_dispositions_json", function (data) {
        var items = [];
        $.each(JSON.parse(data), function (index, dict) {
            items.push("<option value='" + dict.id + "'>" + dict.name + "</option>");
        });
        $parent.find('.new-discrepancy-disposition').last().append(items.join(""));
    });
    $parent.find('input').enterKey(function () {
        saveNewDiscrepancy($parent.find('.new-discrepancy .editable-submit')[0], parent_id, parent_class)
    }).escKey(function () {
        cancelNewDiscrepancy($parent.find('.new-discrepancy .editable-cancel')[0]);
    })
    setTimeout(function () {
        $parent.find('.new-discrepancy-description').focus()
    }, 0);
}

function cancelNewDiscrepancy(e) {
    var $table = $(e).parents('table');
    $(e).parents('.new-discrepancy').remove();
    if ($table.find('.no-discrepancies-added').length == 1) { // This class is only present when no discrepancies have been added
        $table.find('.no-discrepancies-added').show();
        $table.find('thead').hide();
    }
}

function saveNewDiscrepancy(e, parent_id, parent_class) {
    var $newDiscrepancy = $(e).parents('.new-discrepancy');
    if ($newDiscrepancy.find('.new-discrepancy-description').val() != '') {
        $.ajax({
            url: '/product/create_discrepancy',
            type: 'POST',
            data: {
                pk: parent_id,
                class: parent_class,
                description: $newDiscrepancy.find('.new-discrepancy-description').val(),
                disposition_id: $newDiscrepancy.find('.new-discrepancy-disposition').val(),
                justification: $newDiscrepancy.find('.new-discrepancy-justification').val(),
                state: $newDiscrepancy.find('.new-discrepancy-state').val()
            },
            success: function (response) {
                var $table = $(e).parents('table');
                $newDiscrepancy.remove();
                $table.find('.no-discrepancies-added').remove();
                $table.find('thead').show();
                $table.find('tbody').append(response);
                highlight($table.find('tbody tr:last'));
                getWorkflowContainer(parent_id, parent_class);
                $.notify('Discrepancy created');
            }
        });
    }
    else {
        cancelNewDiscrepancy(e);
    }
}

function editDiscrepancy(discrepancy_id, parent_id, parent_class) {
    $('#discrepancy-row-' + discrepancy_id).find(".inline-discrepancy-display").hide();
    $('#discrepancy-row-' + discrepancy_id).find(".action-icons").hide();
    $('#discrepancy-row-' + discrepancy_id).find(".inline-discrepancy-input").show();
    $('#discrepancy-row-' + discrepancy_id).find(".save-icon").show();
    $('#discrepancy-row-' + discrepancy_id).find(".inline-discrepancy-input").enterKey(function () {
        saveDiscrepancy(discrepancy_id, parent_id, parent_class);
    }).escKey(function () {
        cancelDiscrepancy(discrepancy_id);
    });
    setTimeout(function () {
        $('#description-discrepancy-' + discrepancy_id).focus().val($('#description-discrepancy-' + discrepancy_id).val())
    }, 0);
}

function cancelDiscrepancy(discrepancy_id) {
    $('#discrepancy-row-' + discrepancy_id).find(".inline-discrepancy-input").hide();
    $('#discrepancy-row-' + discrepancy_id).find(".save-icon").hide();
    $('#discrepancy-row-' + discrepancy_id).find(".inline-discrepancy-display").show();
    $('#discrepancy-row-' + discrepancy_id).find(".action-icons").show();
    $('#description-discrepancy-' + discrepancy_id).val($('#current-discrepancy-description-' + discrepancy_id).val());
    $('#disposition-discrepancy-' + discrepancy_id).val($('#current-discrepancy-disposition-' + discrepancy_id).val());
    $('#justification-discrepancy-' + discrepancy_id).val($('#current-discrepancy-justification-' + discrepancy_id).val());
    $('#state-discrepancy-' + discrepancy_id).val($('#current-discrepancy-state-' + discrepancy_id).val());
    $('#discrepancy-row-' + discrepancy_id).find(".inline-discrepancy-input").unbind('keydown');
}

function saveDiscrepancy(discrepancy_id, parent_id, parent_class) {
    let $description = $('#description-discrepancy-' + discrepancy_id);
    let $disposition = $('#disposition-discrepancy-' + discrepancy_id);
    let $justification = $('#justification-discrepancy-' + discrepancy_id);
    let $state = $('#state-discrepancy-' + discrepancy_id);
    let description = $('#current-discrepancy-description-' + discrepancy_id).val();
    let disposition = $('#current-discrepancy-disposition-' + discrepancy_id).val();
    let justification = $('#current-discrepancy-justification-' + discrepancy_id).val();
    let state = $('#current-discrepancy-state-' + discrepancy_id).val();
    if ($description.val() !== description || $disposition.val() !== disposition || $justification.val() !== justification || $state.val() !== state) {
        $.ajax({
            url: "/product/update_discrepancy",
            type: 'POST',
            data: {
                pk: discrepancy_id,
                parent_id: parent_id,
                parent_class: parent_class,
                description: $description.val(),
                disposition: $disposition.val(),
                justification: $justification.val(),
                state: $state.val()
            },
            success: function (response) {
                $('#discrepancy-row-' + discrepancy_id).replaceWith(response);
                highlight($('#discrepancy-row-' + discrepancy_id));
                getWorkflowContainer(parent_id, parent_class);
                $.notify('Discrepancy updated');
            }
        });
    }
    else {
        cancelDiscrepancy(discrepancy_id);
    }
}

// Approver related functions
function addApprover(e, parent_id, parent_class) {
    $(e).parents('table').find('.no-approvers-added').hide();
    $(e).parents('table').find('thead').show();
    const $parent = $(e).parents('table').find('tbody');
    let html = '<tr class="new-approver"><td>';
    html += '<select class="form-control input-sm new-approver-approver"><option value="None">---</option></select>';
    html += '</td><td>';
    html += '<input type="text" class="form-control input-sm new-approver-capacity" placeholder="Capacity">';
    html += '</td><td></td>';
    html += '<td width="100px">';
    html += '<div class="save-icon text-right"><div class="editable-buttons">';
    html += '<button type="submit" class="btn btn-primary btn-sm editable-submit" onclick="saveNewApprover(this, ' + parent_id + ', \'' + parent_class + '\')"><i class="glyphicon glyphicon-ok"></i></button>';
    html += '<button type="button" class="btn btn-default btn-sm editable-cancel" onclick="cancelNewApprover(this);"><i class="glyphicon glyphicon-remove"></i></button>';
    html += '</div></div></td></tr>';
    $parent.append(html);
    $.getJSON("/common/get_users_json", function (data) {
        let items = [];
        $.each(JSON.parse(data), function (index, dict) {
            items.push("<option value='" + dict.id + "'>" + dict.name + "</option>");
        });
        $parent.find('.new-approver-approver').last().append(items.join(""));
    });
    $parent.find('input').enterKey(function () {
        saveNewApprover($parent.find('.new-approver .editable-submit')[0], parent_id, parent_class)
    }).escKey(function () {
        cancelNewApprover($parent.find('.new-approver .editable-cancel')[0]);
    });
}

function cancelNewApprover(e) {
    const $table = $(e).parents('table');
    $(e).parents('.new-approver').remove();
    if ($table.find('.no-approvers-added').length === 1) { // This class is only present when no discrepancies have been added
        $table.find('.no-approvers-added').show();
        $table.find('thead').hide();
    }
}

function saveNewApprover(e, parent_id, parent_class) {
    const $newApprover = $(e).parents('.new-approver');
    if ($newApprover.find('.new-approver-capacity').val() !== '' && $newApprover.find('.new-approver-approver').val() !== 'None') {
        $.ajax({
            url: '/common/add_approver',
            type: 'POST',
            data: {
                pk: parent_id,
                class: parent_class,
                approver_id: $newApprover.find('.new-approver-approver').val(),
                capacity: $newApprover.find('.new-approver-capacity').val()
            },
            success: function (response) {
                const $table = $(e).parents('table');
                $newApprover.remove();
                $table.find('.no-approvers-added').remove();
                $table.find('thead').show();
                $table.find('tbody').append(response);
                highlight($table.find('tbody tr:last'));
                getWorkflowContainer(parent_id, parent_class);
                $.notify('Approver added');
            }
        });
    }
    else {
        cancelNewApprover(e);
    }
}

function editApprover(approver_id, parent_id, parent_class) {
    const $approverRow = $('#approver-row-' + approver_id);
    $approverRow.find(".inline-approver-display").hide();
    $approverRow.find(".action-icons").hide();
    $approverRow.find(".inline-approver-input").show();
    $approverRow.find(".save-icon").show();
    $approverRow.find(".inline-approver-input").enterKey(function () {
        saveApprover(approver_id, parent_id, parent_class);
    }).escKey(function () {
        cancelApprover(approver_id);
    });
}

function cancelApprover(approver_id) {
    const $approverRow = $('#approver-row-' + approver_id);
    $approverRow.find(".inline-approver-input").hide();
    $approverRow.find(".save-icon").hide();
    $approverRow.find(".inline-approver-display").show();
    $approverRow.find(".action-icons").show();
    $('#approver-approver-' + approver_id).val($('#current-approver-approver-' + approver_id).val());
    $('#capacity-approver-' + approver_id).val($('#current-approver-capacity-' + approver_id).val());
    $approverRow.find(".inline-approver-input").unbind('keydown');
}

function deleteApprover(event, approver_id, parent_id, parent_class) {
    const $parent = $(event.currentTarget).parents('.list-row');
    const $parentparent = $(event.currentTarget).parents('.list-row').parents('.pri-list');
    $.ajax({
        url: '/common/delete_approver',
        type: 'POST',
        data: {
            approver_id: approver_id,
            parent_id: parent_id,
            parent_class: parent_class
        },
        success: function (result) {
            $parent.remove();
            getWorkflowContainer(parent_id, parent_class);
            $.notify('Approver removed');
            if ($parentparent.find('tr').length === 0) {
                $parentparent.append('<tr class="no-approvers-added"><td colspan="3"><i>No approvers added yet.</i></td></tr>');
            }
        }
    });
}

function saveApprover(approver_id, parent_id, parent_class) {
    const approver = $('#current-approver-approver-' + approver_id).val();
    const capacity = $('#current-approver-capacity-' + approver_id).val();
    const $approver_el = $('#approver-approver-' + approver_id);
    const $capacity_el = $('#capacity-approver-' + approver_id);
    if (($approver_el.val() !== approver  || $capacity_el.val() !== capacity) && $approver_el.val() !== 'None') {
        $.ajax({
            url: "/common/update_approver",
            type: 'POST',
            data: {
                approver_id: approver_id,
                parent_id: parent_id,
                parent_class: parent_class,
                approver: $approver_el.val(),
                capacity: $capacity_el.val(),
            },
            success: function (response) {
                $('#approver-row-' + approver_id).replaceWith(response);
                highlight($('#approver-row-' + approver_id));
                $.notify('Approver updated');
            }
        });
    }
    else {
        cancelApprover(approver_id);
    }
}

function selfApprove(el, parent_id, parent_class) {
    let approve = false;
    if($(el).is(':checked')) {
        approve = true;
    }
    $.ajax({
        url: "/common/self_approve",
        type: 'POST',
        data: {
            parent_id: parent_id,
            parent_class: parent_class,
            approve: approve
        },
        success: function (response) {
            if (approve) {
                $('#approver_list').hide();
            } else {
                $('#approver_list').show();
            }
            getWorkflowContainer(parent_id, parent_class);
        }
    });
}

function getWorkflowContainer(record_id, record_class) {
    if (record_class === Build || record_class === VendorBuild)
        return;
    $.ajax({
        url: '/common/get_workflow_container',
        type: 'POST',
        data: {
            record_id: record_id,
            record_class: record_class
        },
        success: function (response) {
            $('#workflow_container').html(response);
        }
    });
}

function editVendorProductSerialNumber(vendor_product_id) {
    const $container = $('#vendor-product-serial-number-container');
    $container.find(".pri-header-select").addClass('no-carat');
    $container.find(".inline-vendor-product-display").hide();
    $container.find(".action-icons").hide();
    $container.find(".inline-vendor-product-input").show();
    $container.find(".save-icon").show();
    $container.find(".inline-vendor-product-input").enterKey(function () {
        saveVendorProductSerialNumber(vendor_product_id);
    }).escKey(function () {
        cancelVendorProductSerialNumber();
    });
    initial_focus($container.find(".inline-vendor-product-input"));
}

function saveVendorProductSerialNumber(vendor_product_id) {
    const $container = $('#vendor-product-serial-number-container');
    const sn = $container.find(".inline-vendor-product-input").val();
    if ($('#current-vendor-product-serial-number').val() !== sn) {
        $.ajax({
            url: "/vendorproduct/update",
            type: 'POST',
            data: {
                pk: vendor_product_id,
                name: 'serial_number',
                value: sn
            },
            success: function (response) {
                window.location = response.url;
            },
            error: function () {
                $.notify('That serial number already is in use for this vendor product', {type: 'danger'});
            }
        });
    }
    else {
        cancelVendorProductSerialNumber();
    }
}

function cancelVendorProductSerialNumber() {
    const $container = $('#vendor-product-serial-number-container');
    $container.find(".pri-header-select").removeClass('no-carat');
    $container.find(".inline-vendor-product-input").hide();
    $container.find(".save-icon").hide();
    $container.find(".inline-vendor-product-display").show();
    $container.find(".action-icons").show();
    $container.find(".inline-vendor-product-input").val($('#current-vendor-product-serial-number').val());
    $container.find(".inline-vendor-product-input").unbind('keydown');
}

// Document related functions
function deleteDocument(event, url) {
    var $parent = $(event.currentTarget).parents('.list-row');
    var $parentparent = $(event.currentTarget).parents('.list-row').parents('.pri-list');
    $.ajax({
        url: url,
        type: 'DELETE',
        success: function (result) {
            $parent.remove();
            $.notify('Document deleted');
            if ($parentparent.find('tr').length == 0) {
                $parentparent.append('<tr class="no-documents-added"><td colspan="3"><i>No documents added yet.</i></td></tr>');
            }
        }
    });
}

function editDocument(document_id, api_url) {
    $('#document-row-' + document_id).find(".inline-document-display").hide();
    $('#document-row-' + document_id).find(".action-icons").hide();
    $('#document-row-' + document_id).find(".inline-document-input").show();
    $('#document-row-' + document_id).find(".save-icon").show();
    $('#description-document-' + document_id).enterKey(function () {
        saveDocument(document_id, api_url);
    }).escKey(function () {
        cancelDocument(document_id);
    })
    setTimeout(function () {
        $('#description-document-' + document_id).focus().val($('#description-document-' + document_id).val())
    }, 0);
}

function cancelDocument(document_id) {
    $('#document-row-' + document_id).find(".inline-document-input").hide();
    $('#document-row-' + document_id).find(".save-icon").hide();
    $('#document-row-' + document_id).find(".inline-document-display").show();
    $('#document-row-' + document_id).find(".action-icons").show();
    $('#description-document-' + document_id).val($('#current-document-description-' + document_id).val());
    $('#description-document-' + document_id).unbind('keydown');
}

function saveDocument(document_id, url) {
    var description = $('#current-document-description-' + document_id).val();
    if ($('#description-document-' + document_id).val() != description) {
        $.ajax({
            url: url,
            type: 'PUT',
            data: {
                description: $('#description-document-' + document_id).val()
            },
            success: function (response) {
                $('#document-row-' + document_id).replaceWith(response);
                highlight($('#document-row-' + document_id));
                $.notify('Document successfully updated');
            }
        });
    }
    else {
        cancelDocument(document_id);
    }
}

// URL related functions
function addURL(e, api_url) {
    $(e).parents('.pri-table').find('.no-urls-added').hide();
    var $parent = $(e).parents('.pri-table').find('.pri-list');
    var html = '<tr class="new-url"><td width="300px">';
    html += '<input type="text" class="form-control input-sm new-url-url" placeholder="Add URL here">';
    html += '</td><td>';
    html += '<input type="text" class="form-control input-sm new-url-description" placeholder="Add description">';
    html += '</td><td width="100px">';
    html += '<div class="save-icon text-right"><div class="editable-buttons">';
    html += '<button type="submit" class="btn btn-primary btn-sm editable-submit" onclick="saveNewURL(this, \'' + api_url + '\')"><i class="glyphicon glyphicon-ok"></i></button>';
    html += '<button type="button" class="btn btn-default btn-sm editable-cancel" onclick="cancelNewURL(this);"><i class="glyphicon glyphicon-remove"></i></button>';
    html += '</div></div></td></tr>';
    $parent.append(html);
    $parent.find('input').enterKey(function () {
        saveNewURL($parent.find('.new-url .editable-submit')[0], api_url)
    }).escKey(function () {
        cancelNewURL($parent.find('.new-url .editable-cancel')[0]);
    })
    setTimeout(function () {
        $parent.find('.new-url-url').focus()
    }, 0);
}

function cancelNewURL(e) {
    var $table = $(e).parents('table');
    $(e).parents('.new-url').remove();
    if ($table.find('tbody tr').length == 1) {
        // Only the hidden no-urls-added left
        $table.find('.no-urls-added').show();
    }
}

function saveNewURL(e, api_url) {
    if ($(e).parents('.new-url').find('.new-url-url').val() != '') {
        $.ajax({
            url: api_url,
            type: 'POST',
            data: {
                url: $(e).parents('.new-url').find('.new-url-url').val(),
                description: $(e).parents('.new-url').find('.new-url-description').val()
            },
            success: function (response) {
                var $table = $(e).parents('table');
                $(e).parents('.new-url').remove();
                $table.find('.no-urls-added').remove();
                $table.find('tbody').append(response);
                highlight($table.find('tbody tr:last'));
                $.notify('Link created');
            }
        });
    }
    else {
        cancelNewURL(e);
    }
}

function deleteURL(event, url) {
    var $parent = $(event.currentTarget).parents('.list-row');
    var $parentparent = $(event.currentTarget).parents('.list-row').parents('.pri-list');
    $.ajax({
        url: url,
        type: 'DELETE',
        success: function (result) {
            $parent.remove();
            $.notify('Link deleted');
            if ($parentparent.find('tr').length == 0) {
                $parentparent.append('<tr class="no-urls-added"><td colspan="3"><i>No URLs added yet.</i></td></tr>');
            }
        }
    });
}

function editURL(url_id, api_url) {
    $('#link-row-' + url_id).find(".inline-link-display").hide();
    $('#link-row-' + url_id).find(".action-icons").hide();
    $('#link-row-' + url_id).find(".inline-link-input").show();
    $('#link-row-' + url_id).find(".save-icon").show();
    $('#link-row-' + url_id).find(".inline-link-input").enterKey(function () {
        saveURL(url_id, api_url);
    }).escKey(function () {
        cancelURL(url_id);
    })
    setTimeout(function () {
        $('#description-link-' + url_id).focus().val($('#description-link-' + url_id).val())
    }, 0);
}

function cancelURL(url_id) {
    $('#link-row-' + url_id).find(".inline-link-input").hide();
    $('#link-row-' + url_id).find(".save-icon").hide();
    $('#link-row-' + url_id).find(".inline-link-display").show();
    $('#link-row-' + url_id).find(".action-icons").show();
    $('#url-link-' + url_id).val($('#current-link-url-' + url_id).val());
    $('#description-link-' + url_id).val($('#current-link-description-' + url_id).val());
    $('#link-row-' + url_id).find(".inline-link-input").unbind('keydown');
}

function saveURL(url_id, url) {
    var current_url = $('#current-link-url-' + url_id).val();
    var description = $('#current-link-description-' + url_id).val();
    if ($('#url-link-' + url_id).val() != current_url || $('#description-link-' + url_id).val() != description) {
        $.ajax({
            url: url,
            type: 'PUT',
            data: {
                url: $('#url-link-' + url_id).val(),
                description: $('#description-link-' + url_id).val()
            },
            success: function (response) {
                $('#link-row-' + url_id).replaceWith(response);
                highlight($('#link-row-' + url_id));
                $.notify('URL successfully updated');
            }
        });
    }
    else {
        cancelURL(url_id);
    }
}

function addNewCompanyToSelects(companyId, companyName) {
    $.each($('[data-company-select]'), function (i, el) {
        var sel = $(el);
        sel.append($('<option></option>').html(companyName).attr('value', companyId));
        var selected = sel.val(); // cache selected value, before reordering
        var opts_list = sel.find('option');
        opts_list.sort(function (a, b) {
            return $(a).text().trim() > $(b).text().trim() ? 1 : -1;
        });
        sel.html('').append(opts_list);
        // Find special entries
        var pri = sel.find('option:contains("PRI")');
        var prilux = sel.find('option:contains("PRLux")');
        var createNew = sel.find('option[value="create-new-company"]');
        var disabled1 = sel.find('option:disabled')[0];
        var disabled2 = sel.find('option:disabled')[1];
        // Remove special entries
        sel.find('option:contains("PRI")').remove();
        sel.find('option:contains("PRLux")').remove();
        sel.find('option:disabled').remove();
        sel.find('option[value="create-new-company"]').remove();
        // Insert special entries at top
        sel.prepend(disabled2);
        sel.prepend(createNew);
        sel.prepend(disabled1);
        sel.prepend(prilux);
        sel.prepend(pri);
        if (selected === 'create-new-company') {
            sel.val(companyId).change(); // set new company selected value and update DB
        }
        else {
            sel.val(selected); // set cached selected value
        }
    });
}

/**
 * Restores advanced search form values and does initial search to show results
 * @param recordType they type of search being performed
 * @param table the DataTable object that holds the search results
 */
function refreshSearchParams(recordType, table) {

    var searchParams = window.location.search.substring(1);

    if (searchParams !== "") {
        var $form = $('#' + recordType + '-search-form');
        var keyValuePairs = decodeURIComponent(searchParams).split('&');
        var hiddenColIdxs = [];

        for (var i = 0; i < keyValuePairs.length; i++) {
            var pair = keyValuePairs[i].split('=');
            var fieldName = pair[0];
            var fieldValue = pair[1];
            var formFieldName = '[name=' + fieldName + ']';
            $form.find(formFieldName).val(fieldValue);
            if ($form.find(formFieldName).attr('type') == 'checkbox') {
                $form.find(formFieldName).prop('checked', true); // To set checkboxes
            }

            // Allows for making search page viewonly where forms are hidden
            // looks for &mode=viewonly in URL parameters
            if (fieldName === 'mode' && fieldValue === 'viewonly') {
                $('.search-forms').addClass('hidden');
            } else if (fieldName === 'hiddenCols') {
                hiddenColIdxs = JSON.parse(fieldValue);
            }
        }
        //Restore column configuration
        table.columns().every(function () {
            if (hiddenColIdxs.indexOf(this.index()) > -1) {
                // Set hidden columns visible = false
                this.visible(false, false);
            } else {
                // Make column visible
                this.visible(true, false);
            }
        });

        // Trigger search by clicking search btn
        $('#search-' + recordType + '-btn').click();
    }

}

/**
 * DataTables render callback that handles rendering <a> tag for advanced search tables. Used in conjunction
 * with table link library so the row redirects to the link href
 * @param colValue
 * @param type
 * @param row
 * @returns {string}
 */
function renderUrlColumn(colValue, type, row) {
    return '<a href="' + row.url + '" target="_blank">' + colValue + '</a>';
}

/**
 * DataTables render callback that handles formatting date column values for advanced search  tables
 * @param rawValue
 */
function renderDateColumn(rawValue) {
    return moment(rawValue).format('YYYY.MM.DD')
}

/**
 * DataTables render callback that handles rendering correct state icon for advanced search tables
 * @param state Object's state
 * @returns {string} <i> tag with correct icon class
 */
function renderStateIcon(state) {
    var stateIconClasses = {
        'planned': 'pri-icons-planned',
        'in work': 'pri-icons-in-work',
        'analysis': 'pri-icons-in-work',
        'inspection': 'pri-icons-inspection',
        'open': 'pri-icons-open',
        'corrective': 'pri-icons-corrective',
        'approval': 'pri-icons-approval',
        'released': 'pri-icons-thumbs-up',
        'approved': 'pri-icons-thumbs-up',
        'closed': 'pri-icons-thumbs-up',
        'complete:s': 'pri-icons-thumbs-up',
        'complete:u': 'pri-icons-thumbs-down',
        'scrapped': 'pri-icons-obsolete',
        'obsolete': 'pri-icons-obsolete'
    };
    return '<i class="pri-state-icon ' + stateIconClasses[state.toLowerCase()] + '"><span>' + state + '</span></i>';
}


/**
 * DataTables render callback that handles rendering correct criticality icon for advanced search tables
 * @param criticality Object's criticality
 * @returns {string} <i> tag with correct icon class
 */
function renderCriticalityIcon(criticality) {
    return '<i class="pri-icons-critical-' + criticality.toLowerCase() + '" style="font-size: 20px;"></i><span style="padding-left: 5px;">' + criticality + '</span>';
}


/**
 * DataTables render callback that handles rendering correct criticality icon for tasks on dashboard
 * @param criticality Object's criticality
 * @returns {string} <i> tag with correct icon class
 */
function renderCriticalityIconForTasks(criticality) {
    var stateIconClasses = {
        'at your leisure': 'odd',
        'important': 'worrisome',
        'urgent': 'serious',
        'sof': 'sof'
    };
    return '<i class="pri-icons-critical-' + stateIconClasses[criticality.toLowerCase().trim()] + '" style="font-size: 20px;"></i><span style="padding-left: 5px;">' + criticality + '</span>';
}


/**
 * Saves query string needed to repopulate a saved advanced search
 * @param e
 * @param dt
 * @param node
 * @param config
 */
function saveAdvancedSearchParams(e, dt, node, config) {
    // TODO: move this to modals.js
    var recordType = $('input[name=searchFormType]:checked').val();
    var searchParams = $('#' + recordType + '-search-form').formSerialize() + '&record_type=' + recordType;
    var hiddenColIdx = [];
    dt.columns().every(function () {
        if (!this.visible()) {
            hiddenColIdx.push(this.index());
        }
    });

    searchParams += '&hiddenCols=' + JSON.stringify(hiddenColIdx);
    let modal_settings = {
        title: 'Save Search',
        overlay: false,
        draggable: 'title',
        width: 400,
        height: 150,
        ajax: {
            url: '/common/get_advanced_search_modal',
            data: {searchParams: searchParams},
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token}
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    saveSearchModal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    saveSearchModal.open()
}

/**
 * Copies current advanced search parameters and url to user's clipboard
 */
function copySearchUrl(e, dt, node, config) {
    var recordType = $('input[name=searchFormType]:checked').val();
    var searchParams = $('#' + recordType + '-search-form').formSerialize() + '&record_type=' + recordType;
    var hiddenColIdx = [];
    dt.columns().every(function () {
        if (!this.visible()) {
            hiddenColIdx.push(this.index());
        }
    });
    searchParams += '&hiddenCols=' + JSON.stringify(hiddenColIdx);
    var url = window.location.origin + window.location.pathname + '?' + searchParams;
    var $clipboard = $('#advanced-search-clipboard');
    $clipboard.val(url).focus().get(0).select();
    document.execCommand("copy");
}

/**
 * Adds generic Save and Copy buttons to DataTables holding advanced search results
 * @param table DataTable to add buttons to
 * @param domId domId of element that buttons will be appended to
 */
function addSaveAndCopyToDataTable(table, domId) {
    var saveAsBtn = new $.fn.dataTable.Buttons(table, {
        buttons: [
            {text: 'Save As', className: 'pri-btn-secondary', action: saveAdvancedSearchParams}
        ]
    });

    var copyBtn = new $.fn.dataTable.Buttons(table, {
        buttons: [
            {text: 'Copy', className: 'pri-btn-secondary', action: copySearchUrl}
        ]
    });

    saveAsBtn.container().appendTo(domId);
    copyBtn.container().appendTo(domId);
}

/**
 * Function to call when starting a search
 */
function start_search() {
    var element = $('#advanced_search_results')
    element.find('.row').css('opacity', 0.2);
    element.addClass('pri-loader transparent');
    document.activeElement && document.activeElement.blur(); // Remove :active from search button
}

/**
 * Function to call when search has returned data
 * @param data Search result data, not needed to process
 */
function search_complete(data) {
    var element = $('#advanced_search_results')
    element.find('.row').css('opacity', 1);
    element.removeClass('pri-loader transparent');
}

/**
 * Sets focus on a given element during for instance an opening of a page or modal
 * @param e Element to give focus
 */
function initial_focus(e) {
    setTimeout(function () {
        $(e).focus()
    }, 0);
}


/**
 * Disables a modal and shows a loader
 * @param e Main element inside jBox modal
 * @param modal Modal to disable, optional paramenter
 */
function disableModal(e, modal) {
    var element = $(e);
    var jbox = element.closest('.jBox-container');
    // Grey out all content in jBox
    element.css('opacity', 0.2);
    jbox.find('.jBox-title').css('opacity', 0.2);
    // Add our loader overlay
    jbox.addClass('pri-loader');
    // Blur all input fields, purely for visual purposes
    jbox.find('input').blur();
    // Disable modal if passed as parameter, to prevent user from closing it while it's working
    if (typeof modal !== 'undefined') {
        modal.disable();
    }
}

/**
 * Enable a modal after having previously disabled it
 * @param e Main element inside jBox modal
 * @param modal Modal to disable, optional paramenter
 */
function enableModal(e, modal) {
    var element = $(e);
    var jbox = element.closest('.jBox-container');
    // Remove anything greyed out
    element.css('opacity', 1);
    jbox.find('.jBox-title').css('opacity', 1);
    // Remove PRI loader overlay
    jbox.removeClass('pri-loader');
    // Enable modal if passed so user can interact with it again
    if (typeof modal !== 'undefined') {
        modal.enable();
    }
}

function bringModalToFront(modal) {
    var jboxes = $('.jBox-Modal');
    var highest = 0;
    for (var i = 0; i < jboxes.length; i++) {
        var zindex = document.defaultView.getComputedStyle(jboxes[i], null).getPropertyValue("z-index");
        if ((zindex > highest) && (zindex != 'auto')) {
            highest = zindex;
        }
    }
    $('#' + modal.id).css('z-index', parseInt(highest) + 1);
}

function updateState(object_class, object_id, state, transition) {
    $.ajax({
        url: '/' + object_class + '/update_state',
        type: 'POST',
        data: {
            parent_id: object_id,
            state: state,
            transition: transition,
            comment: null
        },
        success: function (response) {
            location.reload();
        }
    });
}

function updateAnomalyDesign(anomaly_id, old_design_id, new_design_id) {
    $.ajax({
        url: '/anomaly/update_design',
        type: 'POST',
        data: {
            anomaly_id: anomaly_id,
            old_design_id: old_design_id,
            new_design_id: new_design_id
        },
        success: function (response) {
            $('#anomaly-design-' + old_design_id).replaceWith(response);
            highlight($('#anomaly-design-' + new_design_id));
        }
    });
}

function removeAnomalyDesign(anomaly_id, design_id, design_class) {
    $.ajax({
        url: '/anomaly/remove_design',
        type: 'POST',
        data: {
            anomaly_id: anomaly_id,
            design_id: design_id,
            design_class: design_class
        },
        success: function (response) {
            $('#anomaly-design-' + design_id).remove();
        }
    });
}

function updateECODesign(eco_id, old_design_id, new_design_id) {
    $.ajax({
        url: '/eco/update_design',
        type: 'POST',
        data: {
            eco_id: eco_id,
            old_design_id: old_design_id,
            new_design_id: new_design_id
        },
        success: function (response) {
            $('#eco-design-' + old_design_id).replaceWith(response);
            highlight($('#eco-design-' + new_design_id));
        }
    });
}

function removeECODesign(eco_id, design_id) {
    $.ajax({
        url: '/eco/remove_design',
        type: 'POST',
        data: {
            eco_id: eco_id,
            design_id: design_id
        },
        success: function (response) {
            $('#eco-design-' + design_id).remove();
        }
    });
}
