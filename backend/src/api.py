import os
import sys
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc, desc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)

cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

def check_keys(obj):
        return all(key in obj for key in ('name', 'color', 'parts'))
    
def get_drink_body():
    body = request.get_json()
    
    title = body.get("title", None)
    recipe = body.get("recipe", [])
    
    if title is None or len(title) < 1:
        abort(400)
    elif len(recipe) == 0:
        abort(400)
    
    recipe_is_invalid = not all(check_keys(recipe_part) for recipe_part in recipe)
    
    if recipe_is_invalid:
        abort(400)
    
    recipe_string = json.dumps(recipe)
    
    return {"title": title, "recipe": recipe_string}

@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add(
        "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
    )
    response.headers.add(
        "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS,PATCH"
    )
    return response


'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
# db_drop_and_create_all()

# ROUTES
#  ----------------------------------------------------------------
#  GETs
#  ----------------------------------------------------------------

@app.route("/drinks")
def get_drinks():
    try:
        drinks = Drink.query.order_by(Drink.id).all()
        
        items = [drink.short() for drink in drinks]
        
        return jsonify({"success": True, "drinks": items})
    except:
        print( sys.exc_info() )
        abort(500)

@app.route("/drinks-detail")
@requires_auth('get:drinks-detail')
def get_detailed_drinks(payload):
    try:
        drinks = Drink.query.order_by(Drink.id).all()
        
        items = [drink.long() for drink in drinks]
        
        return jsonify({"success": True, "drinks": items})
    except:
        print( sys.exc_info() )
        abort(500)

#  ----------------------------------------------------------------
#  POST
#  ----------------------------------------------------------------

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(payload):
    body = get_drink_body()
    
    try:
        drink = Drink()
        drink.title = body["title"]
        drink.recipe = body["recipe"]
    
        drink.insert()
        
        last_drink = Drink.query.order_by(Drink.id.desc()).first()
        
        return jsonify({"success": True, "drinks": [last_drink.long()]})
    except:
        print( sys.exc_info() )
        abort(500)

#  ----------------------------------------------------------------
#  PATCH
#  ----------------------------------------------------------------

@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    
    current_drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    
    if current_drink is None:
        abort(404)
        
    body = get_drink_body()
    
    current_drink.title = body["title"]
    current_drink.recipe = body["recipe"]
    
    try:
        current_drink.update()
        
        drink = Drink.query.get(drink_id)
        
        return jsonify({"success": True, "drinks": [drink.long()]})
    except:
        print( sys.exc_info() )
        abort(500)

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    
    current_drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    
    if current_drink is None:
        abort(404)
        
    try:
        current_drink.delete()
        
        return jsonify({"success": True, "delete": drink_id})
    except:
        print( sys.exc_info() )
        abort(500)

# Error Handling
@app.errorhandler(400)
def bad_request(error):
    return (
        jsonify({
            "success": False, 
            "error": 400, 
            "message": "Bad Request"
        }), 400,
    )
        
@app.errorhandler(401)
def non_valid_authentication(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": error.description
    }), 401

@app.errorhandler(404)
def not_found(error):
    return (
        jsonify({
            "success": False, 
            "error": 404, 
            "message": "Resource not found"
        }), 404,
    )

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": error.description
    }), 500

'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
