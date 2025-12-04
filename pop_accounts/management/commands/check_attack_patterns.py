from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta
from collections import Counter
from pop_accounts.models import PopUpCustomerProfile, PopUpCustomerIP, PopUpPasswordResetRequestLog


class Command(BaseCommand):
    help = "Check for attack patterns in registration and password resets"

    def handle(self, *args, **options):
        recent = now() - timedelta(hours=24)

        # check registration patterns
        recent_registrations = PopUpCustomerIP.objects.filter(
            created_at__gte=recent
        ).values_list('country', 'ip_address')

        country_counts = Counter([r[0] for r in recent_registrations])
        ip_counts = Counter([r[1] for r in recent_registrations])

        # Alert on suspicious patterns
        for country, count in country_counts.items():
            if count > 10:
                self.stdout.write(self.style.WARNING(
                    f"High Registration Volume From {country}: {count} registrations"
                ))
        
        for ip, count, in ip_counts.items():
            if count > 5:
                self.stdout.write(
                    self.style.ERROR(
                        f"Multiple regstrations from {ip}: {count} accounts"
                    )
                )
        
        # check password reset patterns
        recent_resets = PopUpPasswordResetRequestLog.objects.filter(
            requested_at__gte=recent
        ).values_list('ip_address')

        reset_ip_counts = Counter([r[0] for r in recent_resets])

        for ip, count in reset_ip_counts.items():
            if count > 10:
                self.stdout.write(
                    self.style.ERROR(
                        f"Password reset abuse from {ip}: {count} requests"
                    )
                )
        
        # Check inactive users (like the nonprofit's Russian signup)
        inactive_old = PopUpCustomerProfile.objects.filter(
            is_active=False,
            created__lt=now() - timedelta(days=7)
        ).count()

        if inactive_old > 50:
            self.stdout.write(
                self.style.WARNING(
                    f" {inactive_old} inactive users older than 7 days"
                )
            )


# remember to set cron job to run daily
# 0 9 * * * cd /path/to/project && python manage.py check_attack_patterns