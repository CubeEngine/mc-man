from urllib import request, urlencode
from bukget.api import get_slug, get_plugin
import json

PLUGIN_URL = "http://api.bukget.org/3/plugins/bukkit/"
DATA = urlencode({"fields": "-logo_full,-server,-logo,-main,-versions.commands,\
                            -versions.permissions,-versions.changelog,\
                            -versions.status,-versions.dbo_version,-versions.slug"})

class Version(object):
    def __init__(self, json):
        self.game_versions = raw_version['game_versions']
        self.filename = raw_version['filename']
        self.hard_dependencies = raw_version['hard_dependencies']
        self.download = raw_version['download']
        self.version_number = raw_version['version']
        self.link = raw_version['link']
        self.timestamp = raw_version['date']
        self.type = raw_version['type']
        self.soft_dependencies = raw_version['soft_dependencies']
        self.md5 = raw_version['md5']
    
class Plugin(object):
    def __init__(self, slug):
        response = request.urlopen(PLUGIN_URL + slug, DATA)
        self.json_object = json.loads(response.readall().decode("utf-8"))
        
        self.website = self.json_object['website']
        self.devbukkit_page = self.json_object['dbo_page']
        self.description = self.json_object['description']
        self.name = self.json_object['plugin_name']
        self.authors = self.json_object['authors']
        self.slug = self.json_object['slug']
        self.categories = self.json_object['categories']
        self.stage = self.json_object['stage']
        self.popularity_monthly = self.json_object['popularity']['monthly']
        self.popularity_weekly = self.json_object['popularity']['weekly']
        self.popularity_daily = self.json_object['popularity']['daily']
        
        self.versions = {}
        for version_json in self.json_object['versions']:
            version = Version(version_json)
            self.versions[version.version_number] = version
        for version in self.versions:
            if vesion.type == "Release":
                self.lastest_version = version
        
    def get_hard_dependencies(self, hard_dependencies = True,version = self.lastest_version):
        if hard_dependencies:
            return set([get_plugin(get_slug(dep)) for dep in version.hard_dependencies])
        else:
            return set([get_plugin(get_slug(dep)) for dep in version.soft_dependencies])
