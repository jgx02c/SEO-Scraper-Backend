from flask import Blueprint, jsonify
from datetime import datetime
import logging
from db import report_collection

logger = logging.getLogger(__name__)

report_bp = Blueprint("report", __name__)

@report_bp.route('/get_report_for_business/<business_id>', methods=['GET'])
def get_report_for_business(business_id):
    try:
        # Query using integer business_id and get just one report
        report = report_collection.find_one({"business_id": int(business_id)})

        if report:
            # Convert ObjectId to string
            report['_id'] = str(report['_id'])
            
            # Handle any $numberInt values if present
            for key, value in report.items():
                if isinstance(value, dict) and '$numberInt' in value:
                    report[key] = int(value['$numberInt'])

            return jsonify({
                "data": report,  # Now returning the report object directly, not in a list
                "timestamp": datetime.utcnow().isoformat()
            }), 200

        return jsonify({
            "error": "No report found for this business",
            "timestamp": datetime.utcnow().isoformat()
        }), 404

    except Exception as e:
        logger.error(f"Error fetching report for business {business_id}: {e}")
        return jsonify({
            "error": f"Error fetching report: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }), 500