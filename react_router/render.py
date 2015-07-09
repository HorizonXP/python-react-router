import os
import sys
import json
from optional_django import staticfiles
from optional_django.serializers import JSONEncoder
from optional_django.safestring import mark_safe
from optional_django import six
from js_host.function import Function
from js_host.exceptions import FunctionError

from react.render import RenderedComponent
from react.exceptions import ComponentSourceFileNotFound
from react.exceptions import ReactRenderingError

from react_router.conf import settings
from react_router.templates import MOUNT_JS
from react_router.bundle import bundle_component

from webpack.compiler import WebpackBundle

class RouteRenderedComponent(RenderedComponent):
    def get_client_asset(self):
        client_asset = None
        bundled_component = self.get_bundle()
        assets = bundled_component.get_assets()
        for asset in assets:
            if asset['path'] == self.path_to_source:
                client_asset = asset
                break
        return client_asset
    def get_var(self):
        client_asset = self.get_client_asset()
        if client_asset:
            return 'client'
        raise Exception("Client asset not found.")

    def render_js(self):
        client_asset = self.get_client_asset()
        if client_asset:
            client_bundle = mark_safe(WebpackBundle.render_tag(client_asset['url']))
        return mark_safe(
            '\n{bundle}\n<script>\n{mount_js}\n</script>\n'.format(
                bundle=client_bundle,
                mount_js=self.render_mount_js(),
                )
            )
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

    if not os.path.isabs(client_path):
        abs_client_path = staticfiles.find(client_path)
        if not abs_client_path:
            raise ComponentSourceFileNotFound(client_path)
        client_path = abs_client_path

    if not os.path.exists(client_path):
        raise ComponentSourceFileNotFound(client_path)

    bundled_component = None
    import re
    client_re = re.compile(r"client-(?:\w*\d*).js",re.IGNORECASE)
    server_re = re.compile(r"server-(?:\w*\d*).js",re.IGNORECASE)
    if bundle or translate:
        bundled_component = bundle_component(path, client_path, translate=translate)
        assets = bundled_component.get_assets()
        for asset in assets:
            m = client_re.search(asset['name'])
            if m:
                client_path = asset['path']
            m = server_re.search(asset['name'])
            if m:
                path = asset['path']

    if json_encoder is None:
        json_encoder = JSONEncoder

    if props is not None:
        serialized_props = json.dumps(props, cls=json_encoder)
    else:
        serialized_props = None

    try:
        location = {
            'pathname': request.path,
            'query': request.GET.dict()
        }
        cbData = json.loads(js_host_function.call(
            path=path,
            location=location,
            serializedProps=serialized_props,
            toStaticMarkup=to_static_markup
        ))
    except FunctionError as e:
        raise six.reraise(ReactRenderingError, ReactRenderingError(*e.args), sys.exc_info()[2])

    if cbData['match']:
        return RouteRenderedComponent(cbData['markup'], client_path, props, serialized_props, bundled_component, to_static_markup)
    else:
        if cbData['redirectInfo']:
            return RouteRedirect(**cbData['redirectInfo'])
        else:
            return RouteNotFound()
