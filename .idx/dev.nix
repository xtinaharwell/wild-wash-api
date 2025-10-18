{ pkgs, ... }: {
  channel = "stable-24.05";

  packages = [
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.python312Packages.django
    pkgs.python312Packages.django-cors-headers
  ];

  env = {};

  idx = {
    extensions = [ ];
    previews = {
      enable = true;
      previews = { };
    };

    workspace = {
      onCreate = { };
      onStart = { };
    };
  };
}
