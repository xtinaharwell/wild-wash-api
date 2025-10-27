from django.contrib.auth import get_user_model

User = get_user_model()
username = "0769760460"
password = "collins879@"
email = "admin@local"

if User.objects.filter(username=username).exists():
    print("User already exists:", username)
else:
    User.objects.create_superuser(username=username, password=password, email=email)
    print("Created superuser:", username)
