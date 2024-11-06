from krita import DockWidgetFactory, DockWidgetFactoryBase, Krita

# installer les dépendances
from .install import install_requirements
install_requirements()

from .youtube_player import YouTubePlayerDocker

DOCKER_ID = 'youtube_player_docker'
instance = Krita.instance()

# Enregistrer le docker uniquement une fois
dock_widget_factory = DockWidgetFactory(
    DOCKER_ID,
    DockWidgetFactoryBase.DockRight,
    YouTubePlayerDocker
)

instance.addDockWidgetFactory(dock_widget_factory)
