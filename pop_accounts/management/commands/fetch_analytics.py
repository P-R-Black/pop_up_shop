# pop_up/management/commands/fetch_analytics.py
from django.core.management.base import BaseCommand
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest
from django.utils import timezone
from datetime import timedelta
import json
import os

class Command(BaseCommand):
    help = 'Fetch daily visitor data from Google Analytics'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=1, help='Number of days to fetch')

    def handle(self, *args, **options):
        # Initialize the Analytics Data API client
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your/service-account-key.json"
        client = BetaAnalyticsDataClient()
        
        property_id = "YOUR_GOOGLE_ANALYTICS_PROPERTY_ID"  # Get this from GA4 settings
        
        # Create the report request
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[{
                "start_date": (timezone.now() - timedelta(days=options['days'])).strftime('%Y-%m-%d'),
                "end_date": timezone.now().strftime('%Y-%m-%d'),
            }],
            dimensions=[{
                "name": "date"
            }],
            metrics=[{
                "name": "activeUsers"
            }, {
                "name": "newUsers"
            }, {
                "name": "sessions"
            }, {
                "name": "screenPageViews"
            }]
        )

        response = client.run_report(request)
        
        # Process the results
        for row in response.rows:
            date = row.dimension_values[0].value
            active_users = row.metric_values[0].value
            new_users = row.metric_values[1].value
            sessions = row.metric_values[2].value
            page_views = row.metric_values[3].value
            
            self.stdout.write(f"Date: {date}, Active Users: {active_users}, New Users: {new_users}, Sessions: {sessions}, Page Views: {page_views}")