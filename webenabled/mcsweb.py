import random
import string
from logging.config import dictConfig

from flask import (Flask, jsonify, make_response, render_template, request,
                   session)

# See: https://www.geeksforgeeks.org/how-to-use-flask-session-in-python-flask/
from flask_session import Session
from mcs_interface import MCSInterface

# Configure logging _before_ creating the app oject
# https://flask.palletsprojects.com/en/2.0.x/logging/
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def clean_request_data(response):
    """When we get a response from the client, it can be a mess
    and wrapped in weird ways.  Clean it up."""

    # Request data comes as binary, convert to text
    data = request.data.decode("utf-8")

    # Request data has quotes around it, remove them.
    if data[0] == '"' and data[len(data) - 1] == '"':
        data = data[1:len(data) - 1]

    # app.app.logger.warning(f'values in request: {key}')
    return data


def get_mcs_interface(request):
    # Do we know who this is?
    uniq_id_str = request.cookies.get("uniq_id")
    app.logger.info(f"Uniq id: {uniq_id_str}")

    # If old user, get stored mcs interface
    if uniq_id_str is not None:
        mcs_interface = session.get(uniq_id_str)
        if mcs_interface is not None:
            app.logger.info("mcs_interface found in session")
            controller_alive = mcs_interface.is_controller_alive()
            if controller_alive:
                app.logger.info("controller alive, returning interface")
                return mcs_interface, uniq_id_str
            else:
                app.logger.info("controller not alive")
        else:
            app.logger.info("mcs_interface is not found in session")
    else:
        app.logger.info("cannot find uniq id in cookies")

    # Don't recognize, create new mcs interface
    mcs_interface = MCSInterface()
    mcs_interface.start_mcs()

    letters = string.ascii_lowercase
    uniq_id_str = ''.join(random.choice(letters) for i in range(10))
    app.logger.info(f"New user with id {uniq_id_str}")
    session[uniq_id_str] = mcs_interface

    return mcs_interface, uniq_id_str


@app.route('/mcs')
def show_mcs_page():
    mcs_interface, uniq_id_str = get_mcs_interface(request)
    if mcs_interface is None:
        app.logger.warn("Unable to load mcs_interface in session")
        return

    img = mcs_interface.get_latest_image()
    scene_list = mcs_interface.get_scene_list()
    rendered_template = render_template(
        'mcs_page.html', unityimg=img, scene_list=scene_list)
    resp = make_response(rendered_template)
    resp.set_cookie("uniq_id", uniq_id_str)

    return resp


@app.route("/keypress", methods=["POST"])
def handle_keypress():
    mcs_interface, _ = get_mcs_interface(request)
    app.logger.warn(f"in handle_keypress {mcs_interface}")
    if mcs_interface is None:
        app.logger.warn("Unable to load mcs_interface")
        return

    key = clean_request_data(request)
    img_name = mcs_interface.perform_action(key)
    app.logger.debug(f"key pressed is {key} img name is {img_name}")
    resp = jsonify(img_name)
    return resp


@app.route("/scene_selection", methods=["POST"])
def handle_scene_selection():
    mcs_interface, _ = get_mcs_interface(request)
    if mcs_interface is None:
        app.logger.warn("Unable to load mcs_interface")
        return

    # Get the scene filename and tell interface to load it.
    scene_filename = clean_request_data(request)
    app.logger.warning(f'opening scene {scene_filename}')
    _, action_list = mcs_interface.load_scene("scenes/" + scene_filename)
    resp = jsonify(action_list=action_list)
    return resp
