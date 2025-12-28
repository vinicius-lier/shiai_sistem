document.addEventListener('DOMContentLoaded', function () {
  // Public nav toggle
  var navToggle = document.querySelector('[data-toggle="menu"]');
  if (navToggle) {
    navToggle.addEventListener('click', function () {
      document.body.classList.toggle('menu-open');
    });
  }

  // Modal helpers
  document.querySelectorAll('[data-open-modal]').forEach(function (trigger) {
    trigger.addEventListener('click', function (event) {
      event.preventDefault();
      var id = trigger.getAttribute('data-open-modal');
      var modal = document.getElementById(id);
      if (modal) modal.classList.add('open');
    });
  });

  document.querySelectorAll('[data-close-modal]').forEach(function (trigger) {
    trigger.addEventListener('click', function () {
      trigger.closest('.modal')?.classList.remove('open');
    });
  });

  // Application shell toggle
  var shellSidebar = document.querySelector('.app-sidebar');
  var shellToggle = document.querySelectorAll('[data-toggle="sidebar"]');
  var shellOverlay = document.querySelector('.app-overlay');

  function closeSidebar() {
    shellSidebar?.classList.remove('is-open');
    shellOverlay?.classList.remove('is-open');
  }

  shellToggle.forEach(function (btn) {
    btn.addEventListener('click', function () {
      shellSidebar?.classList.toggle('is-open');
      shellOverlay?.classList.toggle('is-open');
    });
  });

  shellOverlay?.addEventListener('click', closeSidebar);

  // Sidebar accordion
  document.querySelectorAll('[data-nav-menu]').forEach(function (btn) {
    btn.addEventListener('click', function (event) {
      event.preventDefault();
      var parent = btn.closest('.nav-item');
      if (!parent) return;
      var isOpen = parent.classList.contains('open');
      document.querySelectorAll('.nav-item.open').forEach(function (item) {
        item.classList.remove('open');
      });
      if (!isOpen) {
        parent.classList.add('open');
      }
    });
  });
});
