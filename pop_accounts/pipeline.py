from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import SocialProfileCompletionForm
from django.contrib.auth import login


def ensure_user_login(strategy, details, response, user=None, *args, **kwargs):
    """
    CRITICAL: Ensure user is logged into the session.
    This fixes the Google OAuth session issue.
    """    
    if not user:
        print("No user provided")
        return {}
    
    request = strategy.request
    
    # CRITICAL FIX: Force login if session doesn't have authenticated user
    if not request.user.is_authenticated or request.user.id != user.id:
        
        # Force login the correct user with the correct backend
        backend_name = kwargs.get('backend').name if kwargs.get('backend') else None
        if backend_name == 'google-oauth2':
            backend_path = 'social_core.backends.google.GoogleOAuth2'
        elif backend_name == 'facebook':
            backend_path = 'social_core.backends.facebook.FacebookOAuth2'
        else:
            backend_path = 'django.contrib.auth.backends.ModelBackend'
        
        login(request, user, backend=backend_path)
        
        
        # Save session explicitly
        request.session.save()
    else:
        print("✅ User already properly authenticated in session")
    
    return {}


def require_profile_completion(strategy, details, user=None, *args, **kwargs):
    """
    Redirect users to a profile completion form if required fields are missing.
    """

    if not user:
        return {}

    # Check if user needs profile completion
    if not user.email or not user.first_name:
        # Save the DB user id so the view can load the right instance
        strategy.session_set('social_profile_user_id', str(user.pk))

        # Pause the pipeline and redirect to complete_profile
        return strategy.redirect(reverse('pop_accounts:complete_profile'))

    return {}

    

def save_social_profile(strategy, details, response, user=None, *args, **kwargs):
    """
    Save extra Google / Facebook profile fields into our custom user model.
    """
    
    if not user:
        return {}

    # Google returns data in `response`
    if kwargs.get("backend").name == "google-oauth2":
        user.email = details.get("email") or user.email
        user.first_name = details.get("first_name") or response.get("given_name") or user.first_name
        user.last_name = details.get("last_name") or response.get("family_name") or user.last_name
        
    # Facebook returns similar data
    elif kwargs.get("backend").name == "facebook":
        user.email = details.get("email") or user.email
        user.first_name = details.get("first_name") or response.get("first_name") or user.first_name
        user.last_name = details.get("last_name") or response.get("last_name") or user.last_name
        

    user.save()
    return {}