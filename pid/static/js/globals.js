
// Default set all x-editables to inline. Needs to be here to be loaded after x-editable is loaded
$.fn.editable.defaults.mode = 'inline';

// Default do not auto discover dropzone
Dropzone.autoDiscover = false;

// Default Datepicker options
$.fn.datepicker.defaults.format = "yyyy-mm-dd";
$.fn.datepicker.defaults.orientation = "bottom auto";
$.fn.datepicker.defaults.maxViewMode = 2;
$.fn.datepicker.defaults.autoclose = true;
$.fn.datepicker.defaults.todayBtn = "linked";
$.fn.datepicker.defaults.todayHighlight = true;

// Default jBox options
let global_jbox_modal_options = {
    preventDefault: true,
    overlay: true,
    closeButton: 'title',
    draggable: 'title',
    position: {x: 'center', y: 'center'}
};
let global_jbox_tooltip_options = {
    attach: '[data-toggle="popover"]',
    addClass: 'pri-jbox',
    closeOnMouseleave: true
};

// Set defaults for Bootstrap Notify
$.notifyDefaults({
    type: 'success',
    delay: 2000,
    offset: { x: 20, y: 60 }
});

// Class names for comparisons. The same as __class__.__name__.lower() or get_class_name()
const Anomaly = 'anomaly';
const AsRun = 'asrun';
const Build = 'build';
const ECO = 'eco';
const Design = 'design';
const Part = 'part';
const Procedure = 'Procedure';
const Product = 'Product';
const Specification = 'specification';
const Task = 'task';
const VendorBuild = 'vendorbuild';
const VendorPart = 'vendorpart';
const VendorProduct = 'vendorproduct';

// CSRF token to use with AJAX requests in jBox since those behave stupidly
const csrf_token = $('meta[name=csrf-token]').attr('content');

const modalMaxHeightScale = 0.66;
