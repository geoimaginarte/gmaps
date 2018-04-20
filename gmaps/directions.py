
import ipywidgets as widgets
import warnings

from traitlets import Bool, Unicode, CUnicode, List, Enum, observe, validate

from . import geotraitlets
from .maps import GMapsWidgetMixin
from ._docutils import doc_subst


ALLOWED_TRAVEL_MODES = {'BICYCLING', 'DRIVING', 'TRANSIT', 'WALKING'}
DEFAULT_TRAVEL_MODE = 'DRIVING'


def _warn_obsolete_data():
    warnings.warn(
        'The "data" traitlet is deprecated, and will be '
        'removed in jupyter-gmaps 0.9.0. '
        'Use "locations" instead.', DeprecationWarning)


def _warn_obsolete_waypoints():
    warnings.warn(
        'Passing "None" to waypoints is deprecated, and will be '
        'removed in jupyter-gmaps 0.9.0. '
        'Pass an empty list.', DeprecationWarning)


_doc_snippets = {}

_doc_snippets['params'] = """
    :param start:
        (Latitude, longitude) pair denoting the start of the journey.
    :type start: 2-element tuple

    :param end:
        (Latitude, longitude) pair denoting the end of the journey.
    :type end: 2-element tuple

    :param waypoints:
        Iterable of (latitude, longitude) pair denoting waypoints.
        Google maps imposes a limitation on the total number of waypoints.
        This limit is currently 23. You cannot use waypoints when the
        travel_mode is ``'TRANSIT'``.
    :type waypoints: List of 2-element tuples, optional

    :param travel_mode:
        Choose the mode of transport. One of ``'BICYCLING'``, ``'DRIVING'``,
        ``'WALKING'`` or ``'TRANSIT'``. A travel mode of ``'TRANSIT'``
        indicates public transportation. Defaults to ``'DRIVING'``.
    :type travel_mode: str, optional

    :param avoid_ferries:
        Avoid ferries where possible.
    :type avoid_ferries: bool, optional

    :param avoid_highways:
        Avoid highways where possible.
    :type avoid_highways: bool, optional

    :param avoid_tolls:
        Avoid toll roads where possible.
    :type avoid_tolls: bool, optional

    :param optimize_waypoints:
        If set to true, will attempt to re-order the supplied intermediate
        waypoints to minimize overall cost of the route.
    :type optimize_waypoints: bool, optional
"""

_doc_snippets['examples'] = """
    >>> fig = gmaps.figure()
    >>> start = (46.2, 6.1)
    >>> end = (47.4, 8.5)
    >>> directions = gmaps.directions_layer(start, end)
    >>> fig.add_layer(directions)
    >>> fig

    You can also add waypoints on the route:

    >>> waypoints = [(46.4, 6.9), (46.9, 8.0)]
    >>> directions = gmaps.directions_layer(start, end, waypoints=waypoints)

    You can choose the travel mode:

    >>> directions = gmaps.directions_layer(start, end, travel_mode='WALKING')

    You can update parameters on an existing layer. This will automatically
    update the map:

    >>> directions.travel_mode = 'DRIVING'
    >>> directions.start = (46.4, 6.1)
"""


class DirectionsServiceException(RuntimeError):
    pass


@doc_subst(_doc_snippets)
class Directions(GMapsWidgetMixin, widgets.Widget):
    """
    Directions layer.

    Add this to a :class:`gmaps.Figure` instance to draw directions.

    Use the :func:`gmaps.directions_layer` factory function to
    instantiate this class, rather than the constructor.

    :Examples:

    {examples}

    {params}
    """
    has_bounds = True
    _view_name = Unicode("DirectionsLayerView").tag(sync=True)
    _model_name = Unicode("DirectionsLayerModel").tag(sync=True)

    start = geotraitlets.Point().tag(sync=True)
    end = geotraitlets.Point().tag(sync=True)
    waypoints = geotraitlets.LocationArray().tag(sync=True)
    data = List(minlen=2, allow_none=True, default_value=None)
    data_bounds = List().tag(sync=True)
    avoid_ferries = Bool(default_value=False).tag(sync=True)
    avoid_highways = Bool(default_value=False).tag(sync=True)
    avoid_tolls = Bool(default_value=False).tag(sync=True)
    optimize_waypoints = Bool(default_value=False).tag(sync=True)
    travel_mode = Enum(
            ALLOWED_TRAVEL_MODES,
            default_value=DEFAULT_TRAVEL_MODE
    ).tag(sync=True)
    show_markers = Bool(default_value=True).tag(sync=True)
    show_route = Bool(default_value=True).tag(sync=True)

    layer_status = CUnicode().tag(sync=True)

    def __init__(self, start=None, end=None, waypoints=None, **kwargs):
        if kwargs.get('data') is not None:
            _warn_obsolete_data()
            # Keep for backwards compatibility with data argument
            data = kwargs['data']
            waypoints = kwargs.get('waypoints')
            if start is None and end is None and waypoints is None:
                start, end, waypoints = Directions._destructure_data(data)
                kwargs.update(
                    dict(start=start, end=end, waypoints=waypoints, data=None))
            else:
                raise ValueError(
                    'Cannot set both data and one of "start", "end"'
                    'or "waypoints".')
        else:
            if waypoints is None:
                waypoints = []
            kwargs.update(dict(start=start, end=end, waypoints=waypoints))
        super(Directions, self).__init__(**kwargs)

    @staticmethod
    def _destructure_data(data):
        start = data[0]
        end = data[-1]
        waypoints = data[1:-1]
        return start, end, waypoints

    @validate('waypoints')
    def _valid_waypoints(self, proposal):
        if proposal['value'] is None:
            _warn_obsolete_waypoints()
            proposal['value'] = []
        return proposal['value']

    @observe('data')
    def _on_data_change(self, change):
        data = change['new']
        if data is not None:
            _warn_obsolete_data()
            with self.hold_trait_notifications():
                self.start, self.end, self.waypoints = \
                        self._destructure_data(data)

    @observe('start', 'end', 'waypoints')
    def _calc_bounds(self, change):
        all_data = [self.start] + self.waypoints + [self.end]
        min_latitude = min(row[0] for row in all_data)
        min_longitude = min(row[1] for row in all_data)
        max_latitude = max(row[0] for row in all_data)
        max_longitude = max(row[1] for row in all_data)
        self.data_bounds = [
            (min_latitude, min_longitude),
            (max_latitude, max_longitude)
        ]


@doc_subst(_doc_snippets)
def directions_layer(
        start, end, waypoints=None, avoid_ferries=False,
        travel_mode=DEFAULT_TRAVEL_MODE,
        avoid_highways=False, avoid_tolls=False, optimize_waypoints=False):
    """
    Create a directions layer.

    Add this layer to a :class:`gmaps.Figure` instance to draw
    directions on the map.

    :Examples:

    {examples}

    {params}

    :returns:
        A :class:`gmaps.Directions` widget.
    """
    kwargs = {
        "start": start,
        "end": end,
        "waypoints": waypoints,
        "travel_mode": travel_mode,
        "avoid_ferries": avoid_ferries,
        "avoid_highways": avoid_highways,
        "avoid_tolls": avoid_tolls,
        "optimize_waypoints": optimize_waypoints
    }
    return Directions(**kwargs)
