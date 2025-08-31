from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import SocialProfileCompletionForm


def require_profile_completion(strategy, details, user=None, *args, **kwargs):
    """
    Redirect users to a profile completion form if required fields are missing.
    """


    if not user:
        return {}

    if not user.email or not user.first_name:
        # Save the DB user id so the view can load the right instance
        strategy.session_set('social_profile_user_id', str(user.pk))

        # Pause the pipeline and redirect to complete_profile
        return strategy.redirect(reverse('pop_accounts:complete_profile'))

    return {}
    