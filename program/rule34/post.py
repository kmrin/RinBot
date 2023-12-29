class Post:
    @staticmethod
    def from_json(json):        
        pFileUrl = json["file_url"]
        pHash = json["hash"]
        pId = json["id"]
        pScore = json["score"]
        pSize = [json["width"], json["height"]]
        pOwner = json["owner"]
        pTags = json["tags"].split(" ")
        preview = json["preview_url"]
        sample = json["sample_url"] # thumbnail
        change = json["change"]
        directory = json["directory"]
        img_type = "video" if pFileUrl.endswith(".mp4") else "gif" if pFileUrl.endswith(".gif") else "image"
        return Post(pId, pHash, pScore, pSize, pFileUrl, preview, sample, pOwner, pTags, img_type, directory, change)
    
    def __init__(self, id: int, hash: str, score: int, size: list, image: str, preview: str, sample: str, owner: str, tags: list, file_type: str, directory: int, change: int):
        self._file_type = file_type
        self._video = ""
        self._image = ""
        if file_type == "image" or file_type == "gif":
            self._image = image
        elif file_type == "video":
            self._video = image
        self._id = id
        self._hash = hash
        self._score = score
        self._size = size # > [WIDTH:int, HEIGHT:int]
        self._preview = preview # thumbnail
        self._sample = sample
        self._owner = owner
        self._tags = tags # > [TAG:str, TAG:str,...]
        self._directory = directory
        self._change = change

    @property
    def id(self) -> int:
        return self._id

    @property
    def hash(self) -> str:
        return self._hash

    @property
    def score(self) -> int:
        return self._score

    @property
    def size(self) -> list:
        return self._size

    @property
    def image(self) -> str:
        return self._image
    
    @property
    def video(self) -> str:
        return self._video
    
    @property
    def thumbnail(self) -> str:
        return self._preview
    
    @property
    def sample(self) -> str:
        return self._sample

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def tags(self) -> list:
        return self._tags

    @property
    def content_type(self) -> str:
        return self._file_type
    
    @property
    def change(self) -> int:
        return self._change
    
    @property
    def directory(self) -> int:
        return self._directory