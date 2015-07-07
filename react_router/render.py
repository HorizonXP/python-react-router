import os
import sys
import json
from optional_django import staticfiles
from optional_django.serializers import JSONEncoder
from optional_django.safestring import mark_safe
from optional_django import six
from js_host.function import Function
from js_host.exceptions import FunctionError

from react.bundle import bundle_component
from react.render import RenderedComponent
from react.exceptions import ComponentSourceFileNotFound
from react.exceptions import ReactRenderingError

from react_router.conf import settings
from react_router.templates import MOUNT_JS

class RouteRenderedComponent(RenderedComponent):
    def render_mount_js(self):
        return mark_safe(
            MOUNT_JS.format(
                var=self.get_var(),
                props=self.serialized_props or 'null',
                container_id=self.get_container_id()
            )
        )

class RouteRedirect(object):
    def __init__(self, pathname, query = None, state = None, *args, **kwargs):
        self.path = pathname
        self.query = query
        if state and 'nextPathname' in state:
            self.nextPath = state['nextPathname']
        else:
            self.nextPath = None
        if self.path is None:
            raise ReactRenderingError("No path returned for redirection.")
        super(RouteRedirect, self).__init__(*args, **kwargs)

    @property
    def url(self):
        if self.query:
            return "%s?next=%s&%s" % (self.path, self.nextPath, self.query)
        else:
            return "%s?next=%s" % (self.path, self.nextPath)

class RouteNotFound(object):
    def __init__(self, *args, **kwargs):
        super(RouteNotFound, self).__init__(*args, **kwargs)

js_host_function = Function(settings.JS_HOST_FUNCTION)

def render_route(
    # Rendering options
    path, # path to routes file
    client_path, # path to client routes file
    request, # pass in request object
    props=None,
    to_static_markup=None,
    # Bundling options
    bundle=None,
    translate=None,
    # Prop handling
    json_encoder=None
):
    if not os.path.isabs(path):
        abs_path = staticfiles.find(path)
        if not abs_path:
            raise ComponentSourceFileNotFound(path)
        path = abs_path

    if not os.path.exists(path):
        raise ComponentSourceFileNotFound(path)

    bundled_component = None
    if bundle or translate:
        bundled_component = bundle_component(path, translate=translate)
        path = bundled_component.get_paths()[0]

    if json_encoder is None:
        json_encoder = JSONEncoder

    if props is not None:
        serialized_props = json.dumps(props, cls=json_encoder)
    else:
        serialized_props = None

    try:
        location = request.path
        cbData = json.loads(js_host_function.call(
            path=path,
            location=location,
            serializedProps=serialized_props,
            toStaticMarkup=to_static_markup
        ))
    except FunctionError as e:
        raise six.reraise(ReactRenderingError, ReactRenderingError(*e.args), sys.exc_info()[2])

    if cbData['match']:
        client_bundled_component = bundle_component(client_path, translate=translate)
        return RouteRenderedComponent(cbData['markup'], client_path, props, serialized_props, client_bundled_component, to_static_markup)
    else:
        if cbData['redirectInfo']:
            return RouteRedirect(**cbData['redirectInfo'])
        else:
            return RouteNotFound()
