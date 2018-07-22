from flask import Blueprint, abort, g
from flask_restful import (Resource, Api, reqparse, fields,
                           url_for, marshal, marshal_with, inputs)

import models
from auth import auth

todo_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'completed': fields.Boolean,
    'edited': fields.Boolean
}


def todo_or_404(todo_id):
    try:
        todo = models.Todo.get(models.Todo.id == todo_id)
    except models.Todo.DoesNotExist:
        abort(404)
    else:
        return todo


class TodoList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'name',
            required=True,
            help="No todo name provided",
            location=['form', 'json']
        )
        self.reqparse.add_argument(
            'completed',
            required=False,
            location=['form', 'json'],
            type=inputs.boolean
        )
        self.reqparse.add_argument(
            'edited',
            required=False,
            location=['form', 'json'],
            type=inputs.boolean
        )
        super(TodoList, self).__init__()

    @auth.login_required
    def get(self):
        return [marshal(todo, todo_fields) for todo in models.Todo.filter(created_by=g.user.id)]

    @marshal_with(todo_fields)
    @auth.login_required
    def post(self):
        args = self.reqparse.parse_args()
        todo = models.Todo.create(
            created_by=g.user.id,
            **args
        )
        return todo, 201, {'Location': url_for('resources.todos.todo', id=todo.id)}


class Todo(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'name',
            required=True,
            help='No todo name provided',
            location=['form', 'json']
        )
        self.reqparse.add_argument(
            'completed',
            required=False,
            location=['form', 'json'],
            type=inputs.boolean
        )
        self.reqparse.add_argument(
            'edited',
            required=False,
            location=['form', 'json'],
            type=inputs.boolean
        )
        super(Todo, self).__init__()

    @marshal_with(todo_fields)
    def get(self, id):
        return todo_or_404(id)

    @marshal_with(todo_fields)
    @auth.login_required
    def put(self, id):
        args = self.reqparse.parse_args()
        query = models.Todo.update(**args).where(models.Todo.id == id)
        query.execute()
        return models.Todo.get(models.Todo.id == id), 200, {'Location': url_for('resources.todos.todo', id=id)}

    @auth.login_required
    def delete(self, id):
        query = models.Todo.delete().where(models.Todo.id == id)
        query.execute()
        return '', 204, {'Location': url_for('resources.todos.todos')}


todos_api = Blueprint('resources.todos', __name__)
api = Api(todos_api)
api.add_resource(
    TodoList,
    '/todos',
    endpoint='todos'
)
api.add_resource(
    Todo,
    '/todos/<int:id>',
    endpoint='todo'
)
