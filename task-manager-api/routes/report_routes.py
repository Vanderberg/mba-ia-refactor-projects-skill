from flask import Blueprint, request, jsonify

from controllers.report_controller import ReportController

report_bp = Blueprint('reports', __name__)
report_controller = ReportController()


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    return jsonify(report_controller.summary_report()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    return jsonify(report_controller.user_report(user_id)), 200


@report_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(report_controller.list_categories()), 200


@report_bp.route('/categories', methods=['POST'])
def create_category():
    return jsonify(report_controller.create_category(request.get_json())), 201


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    return jsonify(report_controller.update_category(cat_id, request.get_json())), 200


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    return jsonify(report_controller.delete_category(cat_id)), 200
