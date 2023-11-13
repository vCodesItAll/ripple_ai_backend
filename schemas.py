from typing import Optional

from pydantic import BaseModel, EmailStr

class AbilityTypeModel(BaseModel):
    id: int
    name: str | None

class AbilityModel(BaseModel):
    id: int
    hero_id: int
    ability_type_id: int
    ability_type: AbilityTypeModel

class RelationshipTypeModel(BaseModel):
    id: int
    name: str | None

class RelationshipModel(BaseModel):
    id: int
    hero1_id: int
    hero2_id: int
    relationship_type_id: int
    relationship_type: RelationshipTypeModel 

class HeroModel(BaseModel):
    id: int
    name: str | None
    about_me: str | None
    biography: str | None
    image_url: str | None
    abilities: list[AbilityModel]
    enemies: list[RelationshipModel]
    friends: list[RelationshipModel]

    def __init__(self, **data):
        super().__init__(**data)
        self.abilities = self.abilities or []
        self.enemies = self.enemies or []
        self.friends = self.friends or []

    class Config:
        from_attributes = True

# class ResponseModel(BaseModel):

#     hero: HeroModel
#     ability: AbilityModel
#     ability_type: AbilityTypeModel