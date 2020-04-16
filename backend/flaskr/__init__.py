import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # Create and configure the app.
    app = Flask(__name__)
    setup_db(app)

    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization, true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, DELETE, OPTIONS')
        return response

    # An endpoint to handle GET requests for all available categories.
    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        category_dict = {category.id: category.type for category in categories}

        return jsonify({
            'success': True,
            'categories': category_dict,
            'total_categories': len(categories)
        })

    # An endpoint to handle GET requests for questions.
    @app.route('/questions')
    def get_questions():
        selection = Question.query.all()
        current_questions = paginate_questions(request, selection)

        categories = Category.query.all()
        category_dict = {category.id: category.type for category in categories}

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': category_dict,
            'current_category': None
        })

    # An endpoint to DELETE question using a question ID.
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id,
                'total_questions': len(Question.query.all())
            })
        except:
            abort(422)

    # An endpoint to POST a new questions
    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', '')
        new_answer = body.get('answer', '')
        new_difficulty = body.get('difficulty', '')
        new_category = body.get('category', '')

        if ((new_question is '') or (new_answer is '') or
                (new_difficulty is '') or (new_category is '')):
            abort(422)

        try:
            question = Question(question=new_question, answer=new_answer,
                                difficulty=new_difficulty, category=new_category)
            question.insert()

            return jsonify({
                'success': True,
                'created': question.id,
                'total_questions': len(Question.query.all())
            }), 201
        except:
            abort(422)

    # A POST endpoint to get questions based on a search term.
    @app.route('/questions/results', methods=['POST'])
    def search_questions():
        body = request.get_json()
        search_term = body.get('searchTerm', None)
        selection = Question.query.filter(
            Question.question.ilike(f'%{search_term}%')).all()

        current_questions = paginate_questions(request, selection)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection)
        })

    # A GET endpoint to get questions based on category.
    @app.route('/categories/<int:category_id>/questions')
    def get_category_questions(category_id):
        category = Category.query.filter(
            Category.id == category_id).one_or_none()

        if category is None:
            abort(404)

        selection = Question.query.filter(
            Question.category == category.id).all()

        current_questions = paginate_questions(request, selection)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'current_category': category.type
        })


    # A POST endpoint to get questions to play the quiz.
    @app.route('/quizzes', methods=['POST'])
    def get_quiz_questions():
        body = request.get_json()

        quiz_category = body.get('quiz_category')
        previous_questions = body.get('previous_questions')

        if ((quiz_category is None) or (previous_questions is None)):
            abort(422)

        if quiz_category['id'] is 0:
            current_questions = Question.query.filter(
                Question.id.notin_(previous_questions)).all()
        else:
            current_questions = Question.query.filter(
                Question.category == quiz_category['id']).filter(
                Question.id.notin_(previous_questions)).all()

        if len(current_questions) > 0:
            question = random.choice(current_questions).format()
        else:
            question = None

        return jsonify({
            'success': True,
            'question': question
        })

    # Error handlers for expected errors.
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'bad request'
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'resource not found'
        }), 404

    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'method not allowed'
        }), 405

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'unprocessable'
        }), 422

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'internal server error'
        }), 500

    return app
