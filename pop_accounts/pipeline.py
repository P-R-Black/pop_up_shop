from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import SocialProfileCompletionForm
from django.contrib.auth import login, get_user_model


User = get_user_model()

def check_required_fields_before_creation(strategy, details, response, user=None, *args, **kwargs):
    """
    Check if we have required fields BEFORE attempting user creation.
    If email or first_name is missing, pause pipeline and redirect to profile completion.
    
    This runs BEFORE create_user, so we can collect missing data without failing.
    """
    # If user already exists, skip this check
    if user:
        return {}
    
    # Get email and first_name from provider response
    email = details.get('email') or response.get('email')
    first_name = details.get('first_name') or response.get('first_name') or response.get('given_name')
    
    # If either is missing, pause pipeline and collect them
    if not email or not first_name:
        # Store what we DO have
        strategy.session_set('social_partial_data', {
            'email': email or '',
            'first_name': first_name or '',
            'last_name': details.get('last_name') or response.get('last_name') or response.get('family_name') or '',
            'backend': kwargs.get('backend').name if kwargs.get('backend') else None
        })
        
        # Redirect to profile completion
        return strategy.redirect(reverse('pop_accounts:complete_profile'))
    
    return {}


def create_user_with_social_data(strategy, details, response, user=None, *args, **kwargs):
    """
    Custom user creation that handles missing email gracefully.
    This replaces the default create_user pipeline step.
    """
    if user:
        return {'is_new': False}
    
    # Get data from details/response
    email = details.get('email') or response.get('email')
    first_name = details.get('first_name') or response.get('first_name') or response.get('given_name')
    last_name = details.get('last_name') or response.get('last_name') or response.get('family_name')
    
    # At this point, email should exist (either from provider or profile completion)
    if not email:
        # This shouldn't happen if check_required_fields_before_creation worked
        raise ValueError("Email is required but not provided by social provider")
    
    # Create user
    user = User.objects.create_user(
        email=email,
        first_name=first_name or '',
        last_name=last_name or '',
    )
    user.is_active = True
    user.save()
    
    return {
        'is_new': True,
        'user': user
    }


def require_profile_completion(strategy, details, response, user=None, *args, **kwargs):
    """
    Redirect users to profile completion if required fields are missing.
    This now runs AFTER user creation for existing users.
    """
    if not user:
        return {}

    # Check if user needs profile completion
    if not user.email or not user.first_name:
        # Save the user ID
        strategy.session_set('social_profile_user_id', str(user.pk))
        
        # Store current data
        strategy.session_set('social_partial_data', {
            'email': user.email or '',
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'backend': kwargs.get('backend').name if kwargs.get('backend') else None
        })

        # Pause and redirect
        return strategy.redirect(reverse('pop_accounts:complete_profile'))

    return {}


def save_social_profile(strategy, details, response, user=None, *args, **kwargs):
    """
    Save extra Google / Facebook profile fields into our custom user model.
    """
    if not user:
        return {}

    backend_name = kwargs.get("backend").name if kwargs.get("backend") else None
    
    # Google
    if backend_name == "google-oauth2":
        user.email = user.email or details.get("email") or response.get("email")
        user.first_name = user.first_name or details.get("first_name") or response.get("given_name")
        user.last_name = user.last_name or details.get("last_name") or response.get("family_name")
        
    # Facebook
    elif backend_name == "facebook":
        user.email = user.email or details.get("email") or response.get("email")
        user.first_name = user.first_name or details.get("first_name") or response.get("first_name")
        user.last_name = user.last_name or details.get("last_name") or response.get("last_name")
    
    # Ensure user is active
    if not user.is_active:
        user.is_active = True
    
    user.save()
    return {}


def ensure_user_login(strategy, details, response, user=None, *args, **kwargs):
    """
    Ensure user is logged into the session.
    """    
    if not user:
        return {}
    
    request = strategy.request
    
    # Force login if not authenticated
    if not request.user.is_authenticated or request.user.id != user.id:
        backend_name = kwargs.get('backend').name if kwargs.get('backend') else None
        
        if backend_name == 'google-oauth2':
            backend_path = 'social_core.backends.google.GoogleOAuth2'
        elif backend_name == 'facebook':
            backend_path = 'social_core.backends.facebook.FacebookOAuth2'
        else:
            backend_path = 'django.contrib.auth.backends.ModelBackend'
        
        login(request, user, backend=backend_path)
        request.session.save()
    
    return {}

    
# def ensure_user_login(strategy, details, response, user=None, *args, **kwargs):
#     """
#     CRITICAL: Ensure user is logged into the session.
#     This fixes the Google OAuth session issue.
#     """    
#     if not user:
#         print("No user provided")
#         return {}
    
#     request = strategy.request
    
#     # CRITICAL FIX: Force login if session doesn't have authenticated user
#     if not request.user.is_authenticated or request.user.id != user.id:
        
#         # Force login the correct user with the correct backend
#         backend_name = kwargs.get('backend').name if kwargs.get('backend') else None
#         if backend_name == 'google-oauth2':
#             backend_path = 'social_core.backends.google.GoogleOAuth2'
#         elif backend_name == 'facebook':
#             backend_path = 'social_core.backends.facebook.FacebookOAuth2'
#         else:
#             backend_path = 'django.contrib.auth.backends.ModelBackend'
        
#         login(request, user, backend=backend_path)
        
        
#         # Save session explicitly
#         request.session.save()
#     else:
#         print("✅ User already properly authenticated in session")
    
#     return {}


# def require_profile_completion(strategy, details, user=None, *args, **kwargs):
#     """
#     Redirect users to a profile completion form if required fields are missing.
#     """

#     if not user:
#         return {}

#     # Check if user needs profile completion
#     if not user.email or not user.first_name:
#         # Save the DB user id so the view can load the right instance
#         strategy.session_set('social_profile_user_id', str(user.pk))

#         # Pause the pipeline and redirect to complete_profile
#         return strategy.redirect(reverse('pop_accounts:complete_profile'))

#     return {}

    

# def save_social_profile(strategy, details, response, user=None, *args, **kwargs):
#     """
#     Save extra Google / Facebook profile fields into our custom user model.
#     """
    
#     if not user:
#         return {}

#     # Google returns data in `response`
#     if kwargs.get("backend").name == "google-oauth2":
#         user.email = details.get("email") or user.email
#         user.first_name = details.get("first_name") or response.get("given_name") or user.first_name
#         user.last_name = details.get("last_name") or response.get("family_name") or user.last_name
        
#     # Facebook returns similar data
#     elif kwargs.get("backend").name == "facebook":
#         user.email = details.get("email") or user.email
#         user.first_name = details.get("first_name") or response.get("first_name") or user.first_name
#         user.last_name = details.get("last_name") or response.get("last_name") or user.last_name
        

#     user.save()
#     return {}