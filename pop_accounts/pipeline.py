from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import SocialProfileCompletionForm
from django.contrib.auth import login


def ensure_user_login(strategy, details, response, user=None, *args, **kwargs):
    """
    CRITICAL: Ensure user is logged into the session.
    This fixes the Google OAuth session issue.
    """
    print("=== ENSURE USER LOGIN ===")
    
    if not user:
        print("No user provided")
        return {}
    
    request = strategy.request
    print(f"User: {user}")
    print(f"User authenticated: {user.is_authenticated}")
    print(f"Session user authenticated: {request.user.is_authenticated}")
    print(f"Session user: {request.user}")
    
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
        
        print(f"   Using backend: {backend_path}")
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

    print("User profile is complete")
    return {}

    # """
    # Redirect users to a profile completion form if required fields are missing.
    # """
    # print("=== REQUIRE PROFILE COMPLETION ===")
    # print("User:", user)
    # print("Details:", details)

    # if not user:
    #     return {}

    # if not user.email or not user.first_name:
    #     # Save the DB user id so the view can load the right instance
    #     strategy.session_set('social_profile_user_id', str(user.pk))

    #     # Pause the pipeline and redirect to complete_profile
    #     return strategy.redirect(reverse('pop_accounts:complete_profile'))

    # # ✅ Ensure user is logged in at this point
    # login(strategy.request, user, backend=user.backend if hasattr(user, 'backend') else 'django.contrib.auth.backends.ModelBackend')

    # return {}
    

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

    # """
    # Save extra Google / Facebook profile fields into our custom user model.
    # """
    # if not user:
    #     return {}

    # # Google returns data in `response`
    # if kwargs.get("backend").name == "google-oauth2":
    #     user.email = details.get("email") or user.email
    #     user.first_name = details.get("first_name") or response.get("given_name") or user.first_name
    #     user.last_name = details.get("last_name") or response.get("family_name") or user.last_name

    #     # Save profile picture if available
    #     # picture_url = response.get("picture")
    #     # if picture_url and not user.profile_image:  # assuming you have profile_image field
    #     #     user.profile_image = picture_url  

    # # Facebook returns similar data
    # elif kwargs.get("backend").name == "facebook":
    #     user.email = details.get("email") or user.email
    #     user.first_name = details.get("first_name") or response.get("first_name") or user.first_name
    #     user.last_name = details.get("last_name") or response.get("last_name") or user.last_name

    #     # Facebook profile picture is nested
    #     picture_data = response.get("picture", {}).get("data", {})
    #     if picture_data.get("url") and not user.profile_image:
    #         user.profile_image = picture_data["url"]

    # user.save()
    # return {}


# def debug_session_and_login(strategy, details, response, user=None, *args, **kwargs):
#     """
#     Debug session state and force login if needed
#     """
#     print("=== DEBUG SESSION AND LOGIN ===")
#     print(f"Backend: {kwargs.get('backend').name}")
#     print(f"User: {user}")
#     print(f"User authenticated: {user.is_authenticated if user else 'No user'}")
    
#     if user:
#         print(f"User ID: {user.id}")
#         print(f"User email: {user.email}")
#         print(f"User first_name: '{user.first_name}'")
#         print(f"User last_name: '{user.last_name}'")
        
#         # Check if user is properly saved in DB
#         from pop_accounts.models import PopUpCustomer
        

#         try:
#             db_user = PopUpCustomer.objects.get(id=user.id)
#             print(f"DB User: {db_user}")
#             print(f"DB User first_name: '{db_user.first_name}'")
#             print(f"DB User email: '{db_user.email}'")
#         except PopUpCustomer.DoesNotExist:
#             print("ERROR: User not found in database!")
        
#         # Check session
#         request = strategy.request
#         print(f"Session key: {request.session.session_key}")
#         print(f"Session authenticated: {request.user.is_authenticated}")
#         print(f"Session user: {request.user}")
        
#         # FORCE login if user isn't authenticated in session
#         if not request.user.is_authenticated:
#             print("WARNING: User not authenticated in session - forcing login")
#             from django.contrib.auth import login
#             login(request, user)
#             print(f"After forced login - Session authenticated: {request.user.is_authenticated}")
#             print(f"After forced login - Session user: {request.user}")
#             print(f"After forced login - Session user first_name: {request.user.first_name}")
        
#     print("==============================")
#     return {}