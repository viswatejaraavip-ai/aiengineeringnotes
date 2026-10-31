(function () {
  // Sidebar toggle on narrow screens.
  var btn = document.querySelector('.menu');
  var nav = document.getElementById('sidenav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // Pages finished in this browser, shown as a tick in the sidebar.
  var KEY = 'aen-done';
  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) { return []; }
  }
  function paint() {
    var done = load();
    var links = document.querySelectorAll('.sidenav a[data-path]');
    for (var i = 0; i < links.length; i++) {
      if (done.indexOf(links[i].getAttribute('data-path')) >= 0) links[i].classList.add('done');
    }
  }
  function markDone() {
    try {
      var done = load();
      var p = location.pathname;
      if (done.indexOf(p) < 0) { done.push(p); localStorage.setItem(KEY, JSON.stringify(done)); paint(); }
    } catch (e) {}
  }
  paint();

  // Remember which shelf the reader is on, for the root page's 'continue' link.
  try { localStorage.setItem('aen-site', location.pathname.indexOf('/dsa/') === 0 ? 'dsa' : 'ai'); } catch (e) {}

  // Remember which branches of the sidebar tree the reader opened or closed.
  // A branch holding the current page always stays open.
  var TREE = 'aen-tree';
  var tree = {};
  try { tree = JSON.parse(localStorage.getItem(TREE) || '{}'); } catch (e) {}
  var branches = document.querySelectorAll('.sidenav details[data-id]');
  for (var b = 0; b < branches.length; b++) {
    (function (d) {
      var id = d.getAttribute('data-id');
      if (!d.querySelector('a.current') && Object.prototype.hasOwnProperty.call(tree, id)) d.open = tree[id];
      d.addEventListener('toggle', function () {
        tree[id] = d.open;
        try { localStorage.setItem(TREE, JSON.stringify(tree)); } catch (e) {}
      });
    })(branches[b]);
  }

  // Reading progress bar; a page counts as read at ninety percent.
  var bar = document.createElement('div');
  bar.className = 'progress';
  document.body.appendChild(bar);
  var marked = false;
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    var p = max > 0 ? h.scrollTop / max : 1;
    bar.style.width = (p * 100) + '%';
    if (p > 0.9 && !marked) { marked = true; markDone(); }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Highlight the current heading in the "On this page" rail.
  var rail = [].slice.call(document.querySelectorAll('.onpage a[href^="#"]'));
  if (rail.length && 'IntersectionObserver' in window) {
    var byId = {};
    rail.forEach(function (a) { byId[a.getAttribute('href').slice(1)] = a; });
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        rail.forEach(function (a) { a.classList.remove('active'); });
        var a = byId[e.target.id];
        if (a) a.classList.add('active');
      });
    }, { rootMargin: '0px 0px -70% 0px' });
    Object.keys(byId).forEach(function (id) {
      var el = document.getElementById(id);
      if (el) obs.observe(el);
    });
  }
})();
