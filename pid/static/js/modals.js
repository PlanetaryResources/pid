
// TODO: Add CSRF token to all requests and change to POST

function addAnomalyModal(class_name, object_id) {
    let modal_settings = {
        width: 800,
        title: 'Create Anomaly',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        ajax: {
            url: '/anomaly/get_create_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                record_id: object_id,
                record_class: class_name
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    // Merge settings with global. From: https://stackoverflow.com/a/171455
    create_anomaly_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    create_anomaly_modal.open();
}

function addDesignToAnomalyModal(anomaly_id) {
    let modal_settings = {
        title: 'Add Design',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        ajax: {
            url: '/anomaly/get_add_design_typeahead_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                anomaly_id: anomaly_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    add_design_to_anomaly_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    add_design_to_anomaly_modal.open();
}

function addDesignToECOModal(eco_id) {
    let modal_settings = {
        title: 'Add Design',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        ajax: {
            url: '/eco/get_add_design_typeahead_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                eco_id: eco_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    add_design_to_eco_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    add_design_to_eco_modal.open();
}

function addECOModal(object_id) {
    let modal_settings = {
        width: 700,
        title: 'Create ECO',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        ajax: {
            url: '/eco/get_create_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                design_id: object_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    create_eco_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    create_eco_modal.open();
}

function addPartModal(part_type, design_id) {
    let title = 'Add Part';
    if (part_type === 'inseparable') {
        title = 'Add Inseparable Component'
    }
    let modal_settings = {
        title: title,
        width: 400,
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        ajax: {
            url: '/part/get_create_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                design_id: design_id,
                part_type: part_type
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    add_part_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    add_part_modal.open();
}

function addPartComponentModal(part_id) {
    let modal_settings = {
        title: 'Add Component',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        ajax: {
            url: '/part/get_add_component_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                part_id: part_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    add_part_component_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    add_part_component_modal.open();
}

function addPartToProcedureModal(procedure_id) {
    let modal_settings = {
        title: 'Add Part',
        addClass: 'procedure-add-part-modal',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        ajax: {
            url: '/procedure/get_add_part_typeahead_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                procedure_id: procedure_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    add_part_to_procedure_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    add_part_to_procedure_modal.open();
}

function addProductComponentModal(product_id) {
    let modal_settings = {
        title: 'Add Component',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        ajax: {
            url: '/product/get_add_product_component_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                product_id: product_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    add_product_components_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    add_product_components_modal.open();
}

function addReferenceModal(class_name, ref_id) {
    let modal_settings = {
        title: 'Add Reference',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        ajax: {
            url: '/common/get_add_reference_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                record_id: ref_id,
                record_class: class_name
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    add_reference_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    add_reference_modal.open();
}

function createAnomalyModal() {
    event.preventDefault();
    let modal_settings = {
        width: 800,
        title: 'Create Anomaly',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        ajax: {
            url: '/anomaly/get_create_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token}
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    create_anomaly_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    create_anomaly_modal.open();
}

function createAsRunModal(procedure_id) {
    let modal_settings = {
        width: 650,
        title: 'Create As-Run',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        ajax: {
            url: '/asrun/get_create_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                procedure_id: procedure_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    create_as_run_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    create_as_run_modal.open();
}

function createCompanyModal() {
    event.preventDefault();
    let modal_settings = {
        width: 650,
        title: 'Create New Company',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/common/add_company_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token}
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    create_company_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    create_company_modal.open();
}

function createDesignModal() {
    event.preventDefault();
    let modal_settings = {
        title: 'Create Design',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/design/get_create_design_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token}
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    create_design_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    create_design_modal.open();
}

function createECOModal() {
    event.preventDefault();
    let modal_settings = {
        width: 700,
        title: 'Create ECO',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        ajax: {
            url: '/eco/get_create_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token}
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    create_eco_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    create_eco_modal.open();
}

function createPartBuildModal(part_id, existing_build_id) {
    let modal_settings = {
        title: 'Create New Build',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/product/build/create',
            reload: 'strict',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                part_id: part_id,
                existing_build_id: existing_build_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
            hardware_type_tooltip.destroy();
        }
    };
    create_part_build_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    create_part_build_modal.open();
}

function createProcedureModal(class_name = null, object_id = null) {
    event.preventDefault();
    let modal_settings = {
        width: 650,
        title: 'Create Procedure',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        ajax: {
            url: '/procedure/get_create_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                table: class_name,
                part_id: object_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
            create_procedure_part_numbers_tooltip.destroy();
        }
    };
    create_procedure_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    create_procedure_modal.open();
}

function createSpecificationModal() {
    event.preventDefault();
    let modal_settings = {
        width: 600,
        title: 'Create Specification',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/specification/get_create_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token}
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    create_specification_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    create_specification_modal.open();
}

function createTaskModal() {
    event.preventDefault();
    let modal_settings = {
        width: 650,
        title: 'Create New Task',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/task/add_task_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token}
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    create_task_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    create_task_modal.open();
}

function createVendorPartModal() {
    event.preventDefault();
    let modal_settings = {
        width: 600,
        title: 'Create Vendor Part',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/vendorpart/get_create_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token}
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    create_vendor_part_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    create_vendor_part_modal.open();
}

function createVendorPartBuildModal(vendor_part_id, existing_build_id) {
    let modal_settings = {
        title: 'Create New Build',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/vendorproduct/build/create',
            reload: 'strict',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                vendor_part_id: vendor_part_id,
                existing_build_id: existing_build_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
            hardware_type_tooltip.destroy();
        }
    };
    create_vendor_build_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    create_vendor_build_modal.open();
}

function reviseDesignModal(design_id) {
    let modal_settings = {
        width: 600,
        title: 'Revise Design',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/design/get_revise_design_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                design_id: design_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    revise_design_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    revise_design_modal.open();
}

function reviseProcedureModal(procedure_id) {
    let modal_settings = {
        width: 600,
        title: 'Revise Procedure',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/procedure/get_revise_procedure_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                procedure_id: procedure_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    revise_procedure_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    revise_procedure_modal.open();
}

function reviseSpecificationModal(specification_id) {
    let modal_settings = {
        width: 600,
        title: 'Revise Specification',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/specification/get_revise_specification_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                specification_id: specification_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    revise_specification_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    revise_specification_modal.open();
}

function selectThumbnailModal(record_id, record_class) {
    let modal_settings = {
        width: 650,
        title: 'Select Thumbnail',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/common/get_thumbnail_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                record_id: record_id,
                record_class: record_class
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    select_thumbnail_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    select_thumbnail_modal.open();
}

function updateProductToRevisionModal(product_id) {
    let modal_settings = {
        title: 'Update Revision',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/product/get_update_product_revision_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                product_id: product_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    update_product_revision_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    update_product_revision_modal.open();
}

function viewChangeLogModal(e) {
    let element = $(e);
    let parent_class = element.attr('data-change-log-class');
    let parent_id = element.attr('data-change-log-id');
    let modal_settings = {
        overlay: false,
        title: 'Change Log',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/common/get_changelog_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                record_id: parent_id,
                record_class: parent_class
            }
        },
        onCloseComplete: function () {
            this.destroy();
            element.data('open', false);
        }
    };
    if (element.data('open') !== true) {
        change_log_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
        change_log_modal.open();
        bringModalToFront(change_log_modal);
        element.data('open', true);
    }
    else {
        pulse($('#' + change_log_modal.id));
        bringModalToFront(change_log_modal);
    }
}

function viewPartBuildsModal(part_id, e) {
    let element = $(e);
    let modal_settings = {
        overlay: false,
        title: 'Existing Builds',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/part/get_view_builds_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                part_id: part_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
            element.data('open', false);
        }
    };
    if (element.data('open') !== true) {
        view_part_builds_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
        view_part_builds_modal.open();
        bringModalToFront(view_part_builds_modal);
        element.data('open', true);
    }
    else {
        pulse($('#' + view_part_builds_modal.id));
        bringModalToFront(view_part_builds_modal);
    }
}

function viewPartNLAModal(part_id, e) {
    let element = $(e);
    let modal_settings = {
        overlay: false,
        title: 'Next Level ASM(s)',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/part/get_view_nlas_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                part_id: part_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
            element.data('open', false);
        }
    };
    if (element.data('open') !== true) {
        view_part_nlas_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
        view_part_nlas_modal.open();
        bringModalToFront(view_part_nlas_modal);
        element.data('open', true);
    }
    else {
        pulse($('#' + view_part_nlas_modal.id));
        bringModalToFront(view_part_nlas_modal);
    }
}

function viewVendorPartBuildsModal(vendor_part_id, e) {
    let element = $(e);
    let modal_settings = {
        overlay: false,
        title: 'Existing Builds',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/vendorpart/get_view_builds_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                vendor_part_id: vendor_part_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
            element.data('open', false);
        }
    };
    if (element.data('open') !== true) {
        view_vendor_part_builds_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
        view_vendor_part_builds_modal.open();
        bringModalToFront(view_vendor_part_builds_modal);
        element.data('open', true);
    }
    else {
        pulse($('#' + view_vendor_part_builds_modal.id));
        bringModalToFront(view_vendor_part_builds_modal);
    }
}

function viewVendorPartNLAModal(vendor_part_id, e) {
    let element = $(e);
    let modal_settings = {
        overlay: false,
        title: 'Next Level ASM(s)',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/vendorpart/get_view_nlas_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                vendor_part_id: vendor_part_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
            element.data('open', false);
        }
    };
    if (element.data('open') !== true) {
        view_vendor_part_nlas_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
        view_vendor_part_nlas_modal.open();
        bringModalToFront(view_vendor_part_nlas_modal);
        element.data('open', true);
    }
    else {
        pulse($('#' + view_vendor_part_nlas_modal.id));
        bringModalToFront(view_vendor_part_nlas_modal);
    }
}

function viewRevisionLogModal(e) {
    let element = $(e);
    let parent_class = element.attr('data-revision-log-class');
    let parent_id = element.attr('data-revision-log-id');
    let modal_settings = {
        width: 600,
        overlay: false,
        title: 'Revision Log',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/common/get_revisionlog_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                record_id: parent_id,
                record_class: parent_class
            }
        },
        onCloseComplete: function () {
            this.destroy();
            element.data('open', false);
        }
    };
    if (element.data('open') !== true) {
        revision_log_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
        revision_log_modal.open();
        bringModalToFront(revision_log_modal);
        element.data('open', true);
    }
    else {
        pulse($('#' + revision_log_modal.id)); // Could also use revision_log_modal.animate('pulseUp');
        bringModalToFront(revision_log_modal);
    }
}

function workflowCommentModal(parent_class, parent_id, state, transition) {
    let modal_settings = {
        width: 600,
        title: transition,
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/common/get_workflow_comment_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                parent_id: parent_id,
                parent_class: parent_class,
                state: state,
                transition: transition
            },
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    workflow_comment_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    workflow_comment_modal.open();
}

function workflowObsoleteModal(parent_class, parent_id, state, transition) {
    let modal_settings = {
        width: 600,
        title: transition,
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/common/get_workflow_obsolete_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                parent_id: parent_id,
                parent_class: parent_class,
                state: state,
                transition: transition
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    workflow_obsolete_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    workflow_obsolete_modal.open();
}

function approvalsModal(parent_id, parent_class) {
    let modal_settings = {
        width: 600,
        title: 'Review',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/common/get_approvals',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                parent_id: parent_id,
                parent_class: parent_class
            }
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    approvals_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    approvals_modal.open();
}

function multipleDesignsCreatedModal(designs) {
    let modal_settings = {
        title: 'Created Designs',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/design/get_multiple_designs_created_modal',
            reload: 'strict',
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            headers: {'X-CSRFToken': csrf_token},
            data: JSON.stringify(designs)
        },
        onCloseComplete: function () {
            this.destroy();
        }
    };
    let multiple_designs_created_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
    multiple_designs_created_modal.open();
}

function viewBuildModal(build_id, e) {
    let element = $(e);
    let modal_settings = {
        overlay: false,
        title: 'Build Information',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/product/get_view_build_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                build_id: build_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
            element.data('open', false);
        }
    };
    if (element.data('open') !== true) {
        view_build_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
        view_build_modal.open();
        bringModalToFront(view_build_modal);
        element.data('open', true);
    }
    else {
        pulse($('#' + view_build_modal.id));
        bringModalToFront(view_build_modal);
    }
}

function viewVendorBuildModal(build_id, e) {
    let element = $(e);
    let modal_settings = {
        overlay: false,
        title: 'Build Information',
        maxHeight: window.innerHeight * modalMaxHeightScale,
        offset: {y: -((window.innerHeight * (1 - modalMaxHeightScale)) / 2) / 2},
        addClass: 'jBox-scroll',
        ajax: {
            url: '/vendorproduct/get_view_vendor_build_modal',
            reload: 'strict',
            type: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            data: {
                build_id: build_id
            }
        },
        onCloseComplete: function () {
            this.destroy();
            element.data('open', false);
        }
    };
    if (element.data('open') !== true) {
        view_vendor_build_modal = new jBox('Modal', $.extend({}, global_jbox_modal_options, modal_settings));
        view_vendor_build_modal.open();
        bringModalToFront(view_vendor_build_modal);
        element.data('open', true);
    }
    else {
        pulse($('#' + view_vendor_build_modal.id));
        bringModalToFront(view_vendor_build_modal);
    }
}
