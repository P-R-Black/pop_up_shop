from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import SocialProfileCompletionForm
from django.contrib.auth import login, get_user_model


User = get_user_model()

# In pipeline.py
def debug_associate_user(*args, **kwargs):
    """Debug wrapper for associate_user"""
    user = kwargs.get('user')
    uid = kwargs.get('uid')
    backend = kwargs.get('backend')
    
    print(f"\n=== associate_user CALLED ===")
    print(f"User: {user}")
    print(f"UID: {uid}")
    print(f"Provider: {kwargs.get('backend').name if kwargs.get('backend') else 'None'}")
    
    # Call original
    from social_core.pipeline.social_auth import associate_user as original
    # result = original(strategy, details, response, user, uid, *args, **kwargs)
    result = original(*args, **kwargs)
    
    print(f"Result: {result}")
    
    # Verify it was created
    if user:
        from social_django.models import UserSocialAuth
        associations = UserSocialAuth.objects.filter(user=user)
        print(f"User now has {associations.count()} social associations")
        for assoc in associations:
            print(f"  ✅ {assoc.provider}: {assoc.uid}")
    else:
        print(f"  ❌ No user to associate!")
    
    print(f"=== associate_user END ===\n")
    return result


def check_required_fields_before_creation(strategy, details, response, user=None, *args, **kwargs):
    """
    Check if we have required fields BEFORE attempting user creation.
    If email or first_name is missing, pause pipeline and redirect to profile completion.
    
    This runs BEFORE create_user, so we can collect missing data without failing.
    """
    print('=== check_required_fields_before_creation ===')

    # ✅ CAPTURE FACEBOOK UID
    facebook_uid = response.get('id')
    print(f'🔑 FACEBOOK UID: {facebook_uid}')  # ← COPY THIS VALUE
    
    print(f'user exists: {user is not None}')


    # If user already exists, skip this check
    if user:
        print('User exists, skipping field check', user)
        strategy.session_pop('social_partial_data')
        strategy.session_pop('social_profile_user_id') 
        return {}
  
    print('User does not exist yet, checking provider data...')
    # Get email and first_name from provider response
    email = details.get('email') or response.get('email')
    print('email from Facebook', email)
    first_name = details.get('first_name') or response.get('first_name') or response.get('given_name')
    print('First name from Facebook', first_name)
    # ✅ NEW: Check if user exists in DB (even without social link)
    # This handles the case where user registered before but lost their social link


    # ✅ NEW: Try to find user by Facebook UID FIRST (more reliable than email)
    if facebook_uid:
        from social_django.models import UserSocialAuth
        try:
            social_auth = UserSocialAuth.objects.get(provider='facebook', uid=facebook_uid)
            existing_user = social_auth.user
            print(f'✅ Found user by Facebook UID: {existing_user.email}')
            return {'user': existing_user}
        except UserSocialAuth.DoesNotExist:
            print('No UserSocialAuth found for this Facebook UID')



    if email:
        try:
            from pop_accounts.models import User
            existing_user = User.objects.get(email__iexact=email)
            print(f'✅ Found existing user by email: {existing_user.email}')
            # Don't pause - let the pipeline link this user
            return {'user': existing_user}  # Pass user to next steps
        except User.DoesNotExist:
            print('No existing user found with this email')

    # If either is missing, pause pipeline and collect them
    if not email or not first_name:
        # Store what we DO have
        print('Missing fields, need to pause pipeline')
        backend = kwargs.get('backend')
        
        # Data to store
        pipeline_data = {
            'backend': backend.name if backend else None,
            'uid': facebook_uid,
            'email': email or '',
            'first_name': first_name or '',
            'last_name': details.get('last_name') or response.get('last_name') or response.get('family_name') or '',
            'details': details,
            'response': {
                'id': facebook_uid,
                'first_name': first_name,
            },
        }
        
        # ✅ Store in BOTH keys for compatibility
        strategy.session_set('paused_pipeline_data', pipeline_data)
        strategy.session_set('social_partial_data', pipeline_data)  # For form pre-fill
        
        print(f'Stored pipeline data in session (both keys)')
        # ✅ NEW: Try to find user by Facebook UID FIRST (more reliable than email)
        if facebook_uid:
            from social_django.models import UserSocialAuth
            try:
                social_auth = UserSocialAuth.objects.get(provider='facebook', uid=facebook_uid)
                existing_user = social_auth.user
                print(f'✅ Found user by Facebook UID: {existing_user.email}')
                return {'user': existing_user}
            except UserSocialAuth.DoesNotExist:
                print('No UserSocialAuth found for this Facebook UID')
        # strategy.session_set('social_partial_data', {
        #     'email': email or '',
        #     'first_name': first_name or '',
        #     'last_name': details.get('last_name') or response.get('last_name') or response.get('family_name') or '',
        #     'backend': kwargs.get('backend').name if kwargs.get('backend') else None
        # })

       
        print(f'Stored paused_pipeline_data in session')
        # Redirect to profile completion
        return strategy.redirect(reverse('pop_accounts:complete_profile'))
    
    
    return {}


def create_user_with_social_data(strategy, details, response, user=None, *args, **kwargs):
    print('create_user_with_social_data hit')
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

    print(f"[PIPELINE] create_user_with_social_data")
    print(f"  Email: {email}")
    print(f"  First: {first_name}")
    print(f"  Last: {last_name}")

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
    
     # Clean up session
    strategy.session_pop('profile_completion_data')
    
    print(f"[PIPELINE] User created: {user.email}")

    
    return {
        'is_new': True,
        'user': user
    }


def require_profile_completion(strategy, details, response, user=None, *args, **kwargs):
    print('require_profile_completion hit')
    """
    Redirect users to profile completion if required fields are missing.
    This now runs AFTER user creation for existing users.
    """

    # DEBUG LOGGING
    print(f"\n=== REQUIRE_PROFILE_COMPLETION ===")
    print(f"User: {user}")
    if user:
        print(f"  Email: '{user.email}' (has value: {bool(user.email)})")
        print(f"  First name: '{user.first_name}' (has value: {bool(user.first_name)})")
        print(f"  Last name: '{user.last_name}' (has value: {bool(user.last_name)})")
        print(f"  Is active: {user.is_active}")
    
    # Check session for stale data
    session_user_id = strategy.session_get('social_profile_user_id')
    print(f"  Session user_id: {session_user_id}")
    print(f"=== END DEBUG ===\n")

    if not user:
        return {}

    # Check if user needs profile completion
    if not user.email or not user.first_name:
        print(f"❌ REDIRECTING to complete_profile")
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
    
    print(f"✅ Profile complete - continuing")
    return {}


def save_social_profile(strategy, details, response, user=None, *args, **kwargs):
    print('save_social_profile')
    """
    Save extra Google / Facebook profile fields into our custom user model.
    """
    print(f"save_social_profile DEBUG: [Facebook] user.email={user.email}, details.email={details.get('email')}, response.email={response.get('email')}")
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
        if not user.first_name and (details.get("first_name") or response.get("first_name")):
            user.first_name = details.get("first_name") or response.get("first_name")
            user.email = user.email or details.get("email") or response.get("email")
            #user.first_name = user.first_name or details.get("first_name") or response.get("first_name")
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


def cleanup_stale_session_data(strategy, details, response, user=None, *args, **kwargs):
    """
    Clean up any stale session data from previous incomplete logins.
    This prevents users from being stuck in profile completion loops.
    """
    # For existing users, clear any stale completion data
    if user:
        strategy.session_pop('social_profile_user_id')
        strategy.session_pop('social_partial_data')
        strategy.session_pop('missing_fields')
    
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