"""Analytics and customer dashboard endpoints."""

from flask import Blueprint, jsonify

from api.services import analytics_service

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api")


def _data_response(data: object):
    return jsonify({"data": data})


@analytics_bp.get("/summary")
def summary():
    return _data_response(analytics_service.get_summary())


@analytics_bp.get("/sales/trend")
def sales_trend():
    return _data_response(analytics_service.get_sales_trend())


@analytics_bp.get("/sales/categories")
def sales_categories():
    return _data_response(analytics_service.get_category_sales())


@analytics_bp.get("/sales/products")
def sales_products():
    return _data_response(analytics_service.get_product_sales())


@analytics_bp.get("/sales/cities")
def sales_cities():
    return _data_response(analytics_service.get_city_sales())


@analytics_bp.get("/customers/segments")
def customer_segments():
    return _data_response(analytics_service.get_customer_segments())


@analytics_bp.get("/customers/churn")
def customer_churn():
    return _data_response(analytics_service.get_churn_statistics())
