from fastapi import HTTPException
from traffic.traffic_service import get_website_traffic_data, get_social_traffic_data, get_ads_traffic_data
from traffic.analytics_service import get_seo_performance_data, get_user_behavior_data, get_competitor_comparison_data

# Get website traffic data
def get_website_traffic(db, user_email):
    traffic_data = get_website_traffic_data(user_email)
    if not traffic_data:
        raise HTTPException(status_code=404, detail="Website traffic data not found")
    return traffic_data


# Get social traffic data
def get_social_traffic(db, user_email):
    social_data = get_social_traffic_data(user_email)
    if not social_data:
        raise HTTPException(status_code=404, detail="Social traffic data not found")
    return social_data


# Get ads traffic data
def get_ads_traffic(db, user_email):
    ads_data = get_ads_traffic_data(user_email)
    if not ads_data:
        raise HTTPException(status_code=404, detail="Ads traffic data not found")
    return ads_data


# Get SEO performance data
def get_seo_performance(db, user_email):
    seo_data = get_seo_performance_data(user_email)
    if not seo_data:
        raise HTTPException(status_code=404, detail="SEO performance data not found")
    return seo_data


# Get user behavior data
def get_user_behavior(db, user_email):
    behavior_data = get_user_behavior_data(user_email)
    if not behavior_data:
        raise HTTPException(status_code=404, detail="User behavior data not found")
    return behavior_data


# Get competitor comparison data
def get_competitor_comparison(db, user_email):
    comparison_data = get_competitor_comparison_data(user_email)
    if not comparison_data:
        raise HTTPException(status_code=404, detail="Competitor comparison data not found")
    return comparison_data
