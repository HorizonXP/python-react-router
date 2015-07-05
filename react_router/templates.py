MOUNT_JS = \
"""
if (typeof {var}.React === 'undefined') throw new Error('Cannot find `React` variable. Have you added an object to your JS export which points to React?');
if (typeof {var}.router === 'undefined') throw new Error('Cannot find `router` variable. Have you added an object to your JS export which points to a function that returns a react-router.Router?');
if (typeof {var} === 'undefined') throw new Error('Cannot find component variable `{var}`');
(function(React, routes, router, containerId) {{
  var props = {props};
  var element = router(routes, props);
  var container = document.getElementById(containerId);
  if (!container) throw new Error('Cannot find the container element `#{container_id}` for component `{var}`');
  React.render(element, container);
}})({var}.React, {var}.routes, {var}.router, '{container_id}');
"""
