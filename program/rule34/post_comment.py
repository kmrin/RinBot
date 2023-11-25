class PostComment:
    def __init__(self, id: int, owner_id:int, body: str, post_id: int, creation: str):
        self._id = id
        self._owner_id = owner_id
        self._body = body
        self._post_id = post_id
        self._creation = creation

    @property
    def id(self) -> int:
        return self._id

    @property
    def author_id(self) -> int:
        return self._owner_id

    @property
    def body(self) -> str:
        return self._body

    @property
    def post_id(self) -> int:
        return self._post_id

    @property
    def creation(self) -> str:
        return self._creation