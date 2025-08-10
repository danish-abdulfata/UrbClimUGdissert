import json
import os

import pytest
from pyproj import CRS
from shapely.geometry import Polygon

from runner.utils import Grid
from runner.utils import Buffer


@pytest.fixture
def grid():
    lon = 3.7216
    lat = -51.0513
    grid = Grid.from_point(
        lon=lon,
        lat=lat,
        nx=3,
        dx=10,
    )
    yield grid


def test_create_grid_from_point(grid):
    assert grid.shape == (3, 3)
    assert grid.step == 10
    assert grid.crs == CRS('EPSG:4326')
    assert len(grid) == 9
    assert grid.bounds.tolist() == pytest.approx([
        3.7213839, -51.05143, 3.721816, -51.051163,
    ])


def test_create_grid_from_polygon():
    poly = Polygon(
        [
            [
                3.5760498046875,
                -50.9930144097952,
            ],
            [
                3.8397216796875,
                -50.9930144097952,
            ],
            [
                3.8397216796875,
                -51.14144802734404,
            ],
            [
                3.5760498046875,
                -51.14144802734404,
            ],
            [
                3.5760498046875,
                -50.9930144097952,
            ],
        ],
    )
    grid = Grid.from_polygon(polygon=poly, nx=5)
    assert grid.shape == (5, 5)
    assert grid.step == pytest.approx(3265.7467)
    assert grid.crs == CRS('EPSG:4326')
    assert len(grid) == 25
    assert grid.bounds.tolist() == pytest.approx(
        [3.59043847, -51.14129156,   3.82570156, -50.99305749],
    )


def test_create_grid_from_polygon_x_smaller_y():
    poly = Polygon(
        [
            [
                3.6639404296874996,
                50.88917404890332,
            ],
            [
                3.779296875,
                50.88917404890332,
            ],
            [
                3.779296875,
                51.12076493195686,
            ],
            [
                3.6639404296874996,
                51.12076493195686,
            ],
            [
                3.6639404296874996,
                50.88917404890332,
            ],
        ],
    )
    grid = Grid.from_polygon(polygon=poly, nx=3)
    assert grid.shape == (3, 3)
    assert grid.step == pytest.approx(2613.7997)
    assert grid.crs == CRS('EPSG:4326')
    assert len(grid) == 9
    assert grid.bounds.tolist() == pytest.approx(
        [3.66523784, 50.969357302, 3.77808415, 51.04055560],
    )


def test_to_file_shp(grid, tmpdir):
    path = tmpdir.mkdir('shp_test')
    grid.to_file(filename=str(path))
    assert set(os.listdir(path)) == {
        'shp_test.shp', 'shp_test.prj', 'shp_test.dbf',
        'shp_test.shx', 'shp_test.cpg',
    }


def test_to_file_custom_kwargs(grid, tmpdir):
    fname = os.path.join(tmpdir, 'test.geojson')
    grid.to_file(filename=fname, index=True)
    assert set(os.listdir(tmpdir)) == {'test.geojson'}
    with open(fname) as f:
        data = json.load(f)

    assert data['features'][0]['properties']['index'] == 0


def test_iterate_file(grid):
    geometries = grid.gdf.geometry.to_list()
    assert geometries == [i[1].geometry for i in grid]


def test_equality_wrong_type(grid):
    assert (grid == 35) is False


def test_equality_true(grid):
    lon = 3.7216
    lat = -51.0513
    new_grid = Grid.from_point(
        lon=lon,
        lat=lat,
        nx=3,
        dx=10,
    )
    assert grid == new_grid


def test_equality_false(grid):
    lon = 3.7217
    lat = -51.0514
    new_grid = Grid.from_point(
        lon=lon,
        lat=lat,
        nx=3,
        dx=10,
    )
    assert grid != new_grid


def test_buffer_from_point():
    buffer = Buffer.from_point(lon=3.7217, lat=51.0514, buffer_rad=500)
    assert len(buffer.gdf) == 1
