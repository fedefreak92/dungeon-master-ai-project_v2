
class AssetManager:
    def __init__(self, base_path=None):
        self.base_path = base_path or 'assets'
        
    def get_asset_path(self, asset_type, asset_id):
        return f"{self.base_path}/{asset_type}/{asset_id}"
