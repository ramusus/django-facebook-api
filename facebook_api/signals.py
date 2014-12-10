from django.dispatch import Signal

#facebook_api_pre_fetch = Signal(providing_args=["instance"])#, "raw", "using", "fetch_fields"])
facebook_api_post_fetch = Signal(providing_args=["instance", "created"])#, "raw", "using", "fetch_fields"])
