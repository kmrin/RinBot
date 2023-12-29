class ICame:
    def __init__(self, character_name:str, count:int):
        self._character_name = character_name
        self._tag_url = "https://rule34.xxx/index.php?page=post&s=list&tags={0}".format(character_name.replace(" ", "_"))
        self._count = count
    
    @property
    def character_name(self) -> str:
        return self._character_name
    
    @property
    def tag_url(self) -> str:
        return self._tag_url

    @property
    def count(self) -> int:
        return self._count