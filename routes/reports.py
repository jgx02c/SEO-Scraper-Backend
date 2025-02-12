from flask import Blueprint, jsonify
from datetime import datetime
import logging
from db import report_collection

logger = logging.getLogger(__name__)

report_bp = Blueprint("report", __name__)

@report_bp.route('/get_reports_for_business/<business_id>', methods=['GET'])
def get_reports_for_business(business_id):
    try:
        # Query using integer business_id, just like in the business route
        reports = list(report_collection.find({"business_id": int(business_id)}))

        if reports:
            # Convert ObjectId to string for each report
            for report in reports:
                report['_id'] = str(report['_id'])
                
                # Handle any $numberInt values if present
                for key, value in report.items():
                    if isinstance(value, dict) and '$numberInt' in value:
                        report[key] = int(value['$numberInt'])

            return jsonify({
                "data": reports,
                "count": len(reports),
                "timestamp": datetime.utcnow().isoformat()
            }), 200

        return jsonify({
            "error": "No reports found for this business",
            "count": 0,
            "timestamp": datetime.utcnow().isoformat()
        }), 404

    except Exception as e:
        logger.error(f"Error fetching reports for business {business_id}: {e}")
        return jsonify({
            "error": f"Error fetching reports: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }), 500