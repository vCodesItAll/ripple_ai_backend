from sqlalchemy.orm import Session, aliased, joinedload
from models import Hero, Ability, AbilityType, Relationship, RelationshipType
from schemas import HeroModel, AbilityModel, AbilityTypeModel, RelationshipModel, RelationshipTypeModel
from sqlalchemy import and_, or_

def create_hero(db: Session, hero: HeroModel):
    db_hero = Hero(name=hero.name, biography=hero.biography, about_me=hero.about_me, image_url=hero.image_url | None )
    db.add(db_hero)
    db.commit()
    db.refresh(db_hero)
    return db_hero

def get_heroes(db: Session):
    FRIENDS_TYPE_ID = 1
    ENEMIES_TYPE_ID = 2

    # Create aliases for the Relationship table
    FriendAlias = aliased(Relationship, name="friend")
    EnemyAlias = aliased(Relationship, name="enemy")

    # Query Heroes and their abilities and ability types
    heroes_with_abilities = (
        db.query(Hero)
        .options(joinedload(Hero.abilities).joinedload(Ability.ability_types))
        .all()
    )

    # Create a mapping of heroes to their models with abilities included
    heroes = {}
    for hero in heroes_with_abilities:
        hid = hero.id
        hero_model = HeroModel(
            id=hero.id,
            name=hero.name,
            about_me=hero.about_me,
            biography=hero.biography,
            image_url=hero.image_url,
            abilities=[
                AbilityModel(
                    id=ability.id,
                    hero_id=hero.id,
                    ability_type_id=ability.ability_type_id,
                    ability_type=AbilityTypeModel(id=ability.ability_type_id, name=ability.ability_types.name)
                )
                for ability in hero.abilities
            ],
            friends=[],
            enemies=[]
        )
        heroes[hid] = hero_model

        # Query Friends and Enemies separately and populate the Hero models
        friends = (
            db.query(Hero, FriendAlias)
            .join(FriendAlias, and_(Hero.id == FriendAlias.hero1_id,
                                    FriendAlias.relationship_type_id == FRIENDS_TYPE_ID))
            .join(RelationshipType, FriendAlias.relationship_type_id == RelationshipType.id)
            .filter(or_(FriendAlias.hero1_id == hid, FriendAlias.hero2_id == hid))
            .all()
        )
        
        for hero, friend in friends:
            friend_model = RelationshipModel(
                id=friend.id,
                hero1_id=friend.hero1_id,
                hero2_id=friend.hero2_id,
                relationship_type_id=friend.relationship_type_id,
                relationship_type=RelationshipTypeModel(id=friend.relationship_type_id, name=friend.relationship_type.name)
            )
            heroes[hid].friends.append(friend_model)

        enemies = (
            db.query(Hero, EnemyAlias)
            .join(EnemyAlias, and_(Hero.id == EnemyAlias.hero1_id,
                                EnemyAlias.relationship_type_id == ENEMIES_TYPE_ID))
            .join(RelationshipType, EnemyAlias.relationship_type_id == RelationshipType.id)
            .filter(or_(EnemyAlias.hero1_id == hid, EnemyAlias.hero2_id == hid))
            .all()
        )

        for hero, enemy in enemies:
            enemy_model = RelationshipModel(
                id=enemy.id,
                hero1_id=enemy.hero1_id,
                hero2_id=enemy.hero2_id,
                relationship_type_id=enemy.relationship_type_id,
                relationship_type=RelationshipTypeModel(id=enemy.relationship_type_id, name=enemy.relationship_type.name)
            )
            # Append the enemy_model to the corresponding hero's enemies list
            heroes[hid].enemies.append(enemy_model)

    # Convert the dictionary to a list of HeroModel instances

    hero_models = list(heroes.values())
    return hero_models