from scene_generator import generate_scene, clean_object


def find_object(id, obj_list):
    for obj in obj_list:
        if obj['id'] == id:
            return obj
    return None


def test_clean_object():
    obj = {
        'id': 'thing1',
        'dimensions': {
            'x': 13,
            'z': 42
        },
        'info': ['a', 'b', 'c', 'd'],
        'info_string': 'abcd',
        'intphys_option': 'stuff',
        'novel_color': True,
        'novel_combination': False,
        'novel_shape': True,
        'shape': 'shape',
        'shows': [{
            'stepBegin': 0,
            'bounding_box': 'dummy'
        }]
    }
    expected = {
        'id': 'thing1',
        'shows': [{
            'stepBegin': 0
        }]
    }
    clean_object(obj)
    assert obj == expected
